
from datetime import datetime, timedelta
import mimetypes


from django.db import models
from django.db.models import Q
from django.db.models import signals
from django.core.urlresolvers import reverse
from django.core.mail import send_mass_mail
from django.core.cache import cache
from django.contrib import messages
from django.db.models.expressions import F
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ugettext_lazy
from django.template.context import RequestContext
from django.template import loader
from django.conf import settings
from django.contrib.auth.models import User
from django import forms

import sphene.community.signals
from sphene.community.middleware import get_current_request, get_current_user, get_current_group, get_current_session
from sphene.community.sphutils import sphpermalink, get_urlconf, get_sph_setting, get_method_by_name
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display
from sphene.community.permissionutils import has_permission_flag
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.models import Group
from sphene.sphblog.utils import slugify
from sphene.sphboard import categorytyperegistry
from renderers import POST_MARKUP_CHOICES, render_body
from sphene.sphboard.signals import clear_post_cache_on_delete, clear_post_cache, clear_category_cache, \
                                    clear_post_4_category_cache, update_category_last_visit_cache, \
                                    clear_category_unread_after_post_move, mark_thread_moved_deleted

import logging
logger = logging.getLogger('sphene.sphboard.models')

"""
Extended Group methods ........
"""

def has_monitor(self):
    return self.__get_monitor(get_current_user())

def has_direct_monitor(self):
    return self.__get_monitor(get_current_user())

def toggle_monitor(self, user=None):
    """Toggles monitor and returns the newly created monitor, or None if an
    existing monitor was deleted."""
    if not user:
        user = get_current_user()
    if self.has_direct_monitor():
        self.has_direct_monitor().delete()
        if hasattr(self, '__monitor'): delattr(self,'__monitor')
    else:
        monitor = Monitor(user = user,
                          group = self, )
        monitor.save()
        self.__monitor = monitor
        return monitor

def __get_monitor(self, user):
    if hasattr(self, '__monitor'): return self.__monitor

    try:
        monitor = Monitor.objects.get( user = user,
                                       group = self,
                                       category__isnull = True,
                                       thread__isnull = True, )
    except Monitor.DoesNotExist:
        monitor = None
    return monitor

Group.has_monitor = has_monitor
Group.has_direct_monitor = has_direct_monitor
Group.toggle_monitor = toggle_monitor
Group.__get_monitor = __get_monitor

"""
END of extended Group methods ...
"""

POSTS_ALLOWED_CHOICES = (
    (-1, 'All Users'),
    (0, 'Loggedin Users'),
    (1, 'Members of the Group'),
    (2, 'Staff Members'),
    (3, 'Nobody'),
    )

class AccessCategoryManager(models.Manager):
    def filter_for_group(self, group):
        user = get_current_user()
        category_ids = get_all_viewable_categories(group, user)
        return self.filter(group = group, id__in = category_ids)

    def rolemember_limitation_objects(self, group):
        return self.filter( group = group )


class CategoryTypeChoices(object):
    def __iter__(self):
        if get_current_request() is None:
            return [].__iter__()
        choices = ()
        try:
            for ct in categorytyperegistry.get_category_type_list():
                choices += ((ct.name, "%s (%s)" % (unicode(ct.label), ct.name)),)
        except:
            # This is also called during syncdb before tables are
            # created, so for this case catch all exceptions.
            # see http://sct.sphene.net/board/thread/898/
            print "Error while trying to fetch category types."
            pass

        return choices.__iter__()
        

def get_category_type_choices():
    """
    This method generates the choices for the 'category_type'
    field of Category entity - this should probably be improved
    to make sure that this method is fully dynamic..
    """
    return CategoryTypeChoices()

def get_tags_for_categories(categories):
    """
    Returns a list of all used tags in the given categories.
    """
    from django.contrib.contenttypes.models import ContentType
    from sphene.community.models import Tag, TagLabel, TaggedItem
    from django.db import connection

    group_ids = list()
    category_ids = list()
    for category in categories:
        group = category.group
        if not group.id in group_ids:
            group_ids.append(group.id)
        category_ids.append(category.id)

    tags = Tag.objects.filter( group__id__in = group_ids )

    qn = connection.ops.quote_name

    content_type = ContentType.objects.get_for_model(Post)
    
    tags = tags.extra(
        tables=[TagLabel._meta.db_table,
                TaggedItem._meta.db_table,
                Post._meta.db_table, ],
        where=[
            '%s.tag_id = %s.%s' % (qn(TagLabel._meta.db_table),
                                   qn(Tag._meta.db_table),
                                   Tag._meta.pk.column),
            '%s.tag_label_id = %s.%s' % (qn(TaggedItem._meta.db_table),
                                         qn(TagLabel._meta.db_table),
                                         TagLabel._meta.pk.column),
            '%s.content_type_id = %%s' % (qn(TaggedItem._meta.db_table)),
            '%s.object_id = %s.%s' % (qn(TaggedItem._meta.db_table),
                                      qn(Post._meta.db_table),
                                      Post._meta.pk.column),
            '%s.category_id IN (%s)' % (qn(Post._meta.db_table), ','.join([str(cid) for cid in category_ids ])),
            ],
        params=[content_type.pk],).order_by('name').distinct()
    

    return tags


def get_all_viewable_categories(group, user):
    """ 
    returns a list containing the IDs of all categories viewable by the given 
    user in the given group.
    (If for_parent is passed in, only categries with the given parent are
    returned.)
    """
    all_categories = Category.objects.filter( group = group )
    allowed_categories = list()
    for category in all_categories:
        if category.has_view_permission( user ):
            allowed_categories.append(category.id)
    return allowed_categories


class Category(models.Model):
    name = models.CharField(max_length = 250)
    group = models.ForeignKey(Group, null = True, blank = True)
    parent = models.ForeignKey('self', related_name = 'subcategories', null = True, blank = True)
    description = models.TextField(blank = True)
    allowview = models.IntegerField( default = -1, choices = POSTS_ALLOWED_CHOICES )
    allowthreads = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    allowreplies = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    sortorder = models.IntegerField( default = 0, null = False )

    slug = models.CharField(max_length = 250, unique = True, db_index = True)

    category_type = models.CharField(max_length = 250, blank = True, db_index = True, choices = get_category_type_choices())

    objects = AccessCategoryManager()#models.Manager()
    sph_objects = AccessCategoryManager()


    changelog = ( ( '2007-04-14 00', 'alter', 'ADD sortorder INTEGER' ),
                  ( '2007-04-14 01', 'update', 'SET sortorder = 0' ),
                  ( '2007-04-14 02', 'alter', 'ALTER sortorder SET NOT NULL' ),
                  
                  ( '2007-09-03 00', 'alter', 'ADD category_type varchar(250)' ),
                  ( '2007-09-03 01', 'update', "SET category_type = ''" ),
                  ( '2007-09-03 02', 'alter', 'ALTER category_type SET NOT NULL' ),

                  ( '2010-06-23 01', 'alter', 'ADD slug varchar(250)' ),
                  ( '2010-06-23 02', 'update', 'SET slug = id' ),
                  ( '2010-06-23 03', 'alter', 'ALTER slug SET NOT NULL'),
                  )

    sph_permission_flags = { 'sphboard_editallposts':
                             ugettext_lazy('Allow editing of all posts.'),

                             'sphboard_annotate':
                             ugettext_lazy('Allow annotating users posts.'),

                             'sphboard_move':
                             ugettext_lazy('Allow moving of threads.'),

                             'sphboard_sticky':
                             ugettext_lazy('Allow marking threads as sticky.'),

                             'sphboard_lock':
                             ugettext_lazy('Allow locking of threads.'),

                             'sphboard_post_threads':
                             ugettext_lazy('Allow creating new threads.'),

                             'sphboard_post_replies':
                             ugettext_lazy('Allow posting of replies to existing threads.'),

                             'sphboard_view':
                             ugettext_lazy('Allows viewing of threads.'),

                             'sphboard_hideallposts':
                             ugettext_lazy('Allows deleting posts.'),

                             'sphboard_moveallposts':
                             ugettext_lazy('Allows moving posts.'),

                             'sphboard_delete_moved_threadinformation':
                             ugettext_lazy('Allows deleting information about moved threads.'),
                             }

    def get_category_type(self):
        if not self.category_type or self.category_type == 'None':
            from sphene.sphboard.categorytypes import DefaultCategoryType
            return DefaultCategoryType( self )
        ct = categorytyperegistry.get_category_type( self.category_type )
        if ct is None:
            raise Exception( 'Invalid category type "%s" for "%s"' % (self.category_type, self.name))
        return ct(self)

    def get_rolemember_limitation_objects(group):
        """
        Tells sphene community objects that this model can be used to limit
        the membership of a user in a given role.
        """
        return Category.objects.filter( group = group )

    def get_children(self):
        """ Returns all children of this category in which the user has view permission. """
        return Category.sph_objects.filter_for_group( self.group ).filter( parent = self )

    def canContainPosts(self):
        return self.allowthreads != 3

    def get_thread_list(self):
        #return self.posts.filter( thread__isnull = True )
        if get_sph_setting( 'workaround_select_related_bug' ):
            # See http://code.djangoproject.com/ticket/4789
            return self.threadinformation_set
        return self.threadinformation_set.filter(root_post__is_hidden = 0).select_related( depth = 1 )

    def _cache_key_thread_count(self):
        return '%s_category_tc_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.pk)

    def threadCount(self):
        key = self._cache_key_thread_count()
        res = cache.get(key)
        if not res:
            res = self.threadinformation_set.filter(root_post__is_hidden=0).count()
            cache.set(key, res)
        return res

    def _cache_key_post_count(self):
        return '%s_category_pc_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.pk)

    def postCount(self):
        key = self._cache_key_post_count()
        res = cache.get(key)
        if not res:
            res = self.posts.filter(is_hidden=0).count()
            cache.set(key, res)
        return res

    def _cache_key_latest_post(self):
        return '%s_category_lp_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.pk)

    def get_latest_post(self):
        key = self._cache_key_latest_post()
        res = cache.get(key)
        if not res:
            try:
                res = self.posts.filter(is_hidden=0).latest( 'postdate' )
                cache.set(key, res)
            except Post.DoesNotExist:
                cache.set(key, None)
        return res

    # For backward compatibility ...
    latestPost = get_latest_post

    def has_post_thread_permission(self, user = None):
        if not user:
            user = get_current_user()
        return self.testAllowance(user, self.allowthreads) \
               or has_permission_flag(user, 'sphboard_post_threads', self)
    allowPostThread = has_post_thread_permission

    def allows_replies(self):
        """
        Returns True if _anyone_ is allowed to post replies
        """
        return self.allowreplies != 3

    def has_view_permission(self, user = None):
        if not user:
            user = get_current_user()
        return self.testAllowance(user, self.allowview) \
               or has_permission_flag(user, 'sphboard_view', self)

    def testAllowance(self, user, level):
        if level == -1:
            return True;
        if user == None or not user.is_authenticated():
            return False;
        if level == 0:
            return True;

        if level == 1 and self.group.get_member(user) != None:
            return True

        if level <= 2 and user.is_staff:
            return True
        
        return False

    def has_permission_flag(self, user, flag):
        return False

    def has_new_posts(self):
        ret = self.hasNewPosts()
        return ret

    def catchup(self, session, user):
        """Marks all posts in the current category as read."""
        ThreadLastVisit.objects.filter( user = user,
                                        thread__category = self, ).delete()
        try:
            categoryLastVisit = CategoryLastVisit.objects.get( category = self,
                                                               user = user, )
            categoryLastVisit.lastvisit = timezone.now()
            categoryLastVisit.oldlastvisit = None
            categoryLastVisit.save()
        except CategoryLastVisit.DoesNotExist:
            return True

    def touch(self, session, user):
        """
        Touches the category object by updating 'lastVisit'
        Returns the datetime object of when it was last visited.
        """
        # Check if we were already "touched" ;)
        if getattr(self, '_touched', False): return self.get_lastvisit_date(user)
        self._touched = True
        self.__hasNewPosts = self._hasNewPosts(session, user)
        if not user.is_authenticated(): return None

        last_visit, created = CategoryLastVisit.objects.get_or_create(user=user, category=self)
        if not created:
            if not last_visit.oldlastvisit and self.__hasNewPosts:
                # Only set oldlastvisit if we have new posts.
                last_visit.oldlastvisit = last_visit.lastvisit
            last_visit.lastvisit = timezone.now()
            last_visit.save()
        last_visit_date = last_visit.oldlastvisit or last_visit.lastvisit
        return last_visit_date

    def _cache_key_lastvisit_date(self, user):
        return '%s_category_lastvisit_date_%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.pk, user.pk)

    def get_lastvisit_date(self, user):
        key = self._cache_key_lastvisit_date(user)
        last_visit_date = cache.get(key)
        if not last_visit_date:
            try:
                last_visit = CategoryLastVisit.objects.get(category=self, user=user)
                last_visit_date = last_visit.oldlastvisit or last_visit.lastvisit
            except CategoryLastVisit.DoesNotExist:
                last_visit_date = timezone.now()
            cache.set(key, last_visit_date)
        return last_visit_date

    def hasNewPosts(self):
        return self._hasNewPosts(get_current_session(), get_current_user())

    def _hasNewPosts(self, session, user):
        if hasattr(self, '__hasNewPosts'): return self.__hasNewPosts
        if not user.is_authenticated(): return False
        latestPost = self.get_latest_post()
        if not latestPost:
            return False
        
        lastvisit = self.get_lastvisit_date(user)

        if lastvisit > latestPost.postdate:
            return False
        return True

    def update_unread_status(self, user):
        """ Check if all threads in current category were read by user
        """
        last_visit_date = self.get_lastvisit_date(user)
        # If there are any threads that were never visited by user and have unread posts then
        # this means that category is unread
        if ThreadInformation.objects.filter(root_post__is_hidden=0,
                                            category=self,
                                            thread_latest_postdate__gt=last_visit_date).exclude(
                                            root_post__threadlastvisit__user=user).exists():
            # there are unread posts - return
            return


        # check if all threads in current category were read:
        # this means that lastvisit date of each thread is newer than postdate of last post in this thread
        has_unread_threads = Post.objects.\
           filter(threadlastvisit__user=user,
                  thread__isnull=True,
                  category=self,
                  threadinformation__thread_latest_postdate__gt=last_visit_date).\
           filter(threadinformation__thread_latest_postdate__gt=F('threadlastvisit__lastvisit')).\
           distinct().\
           exists()

        if has_unread_threads:
            return

        # All posts are read .. cool.. we can remove all ThreadLastVisit and adapt CategoryLastVisit
        ThreadLastVisit.objects.filter(user=user,
                                       thread__category=self).delete()
        clv = CategoryLastVisit.objects.get(category = self, user=user)
        clv.oldlastvisit = None
        clv.save()

    def toggle_monitor(self, user=None):
        """Either creates a monitor if there is none currently, or deletes an
        existing monitor."""
        if not user:
            user = get_current_user()
        
        if self.has_direct_monitor():
            self.__get_monitor(user).delete()
            if hasattr(self, '__monitor'): delattr(self,'__monitor')
        else:
            monitor = Monitor(group = self.group,
                              user = user,
                              category = self)
            monitor.save()
            self.__monitor = monitor
            return monitor

    def has_monitor(self):
        """Returns True if there is a monitor for
        the current user in the current category or any parent category."""
        monitor = self.__get_monitor(get_current_user())
        return monitor

    def has_direct_monitor(self):
        """Only return True if there is a direct monitor for the current
        category."""
        monitor = self.__get_monitor(get_current_user())
        return monitor and monitor.category == self

    def __get_monitor(self, user):
        if hasattr(self, '__monitor'): return self.__monitor
        try:
            monitor = Monitor.objects.get( category = self,
                                           user = user,
                                           thread__isnull = True, )
        except Monitor.DoesNotExist:
            if self.parent:
                monitor = self.parent.has_monitor()
            else:
                monitor = self.group.has_monitor()

        self.__monitor = monitor
        return self.__monitor

    def get_absolute_url(self):
        cturl = self.get_category_type().get_absolute_url_for_category()
        if cturl:
            return cturl
        return self._get_absolute_url()

    def _cache_key_absolute_url(self):
        return '%s_cat_abs_url_%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.pk, get_sph_setting('board_slugify_links'))

    def _get_absolute_url(self):
        key = self._cache_key_absolute_url()
        res = cache.get(key)
        if not res:
            kwargs = { 'groupName': self.group.name,
                       'category_id': self.id }
            if get_sph_setting('board_slugify_links'):
                kwargs['slug'] = slugify(self.name) or '_'
                name = 'sphboard_show_category'
            else:
                name = 'sphboard_show_category_without_slug'
            res = (name, (), kwargs)
            cache.set(key, res)
        return res
    _get_absolute_url = sphpermalink(_get_absolute_url)

    def get_absolute_post_thread_url(self):
        return ('sphboard_post_thread', (), { 'groupName': self.group.name, 'category_id': self.id })
    get_absolute_post_thread_url = sphpermalink(get_absolute_post_thread_url)

    def get_absolute_url_rss_latest_threads(self):
        """ Returns the absolute url to the RSS feed displaying the latest threads.
        This will only work since django changeset 4901 (>0.96) """
        return reverse( 'sphboard-feeds',
                        urlconf = get_urlconf(),
                        kwargs = { 'category_id': self.id } )

    def get_absolute_latest_url(self):
        return ('sphboard_latest', (), { 'groupName': self.group.name, 'category_id': self.id, })
    get_absolute_latest_url = sphpermalink(get_absolute_latest_url)

    def get_absolute_togglemonitor_url(self):
        return ('sphene.sphboard.views.toggle_monitor', (), { 'groupName': self.group.name, 'monitortype': 'category', 'object_id': self.id, })
    get_absolute_togglemonitor_url = sphpermalink(get_absolute_togglemonitor_url)
    
    def __unicode__(self):
        return self.name;

    class Meta:
        verbose_name = ugettext_lazy('Category')
        verbose_name_plural = ugettext_lazy('Categories')
        ordering = ['sortorder']


class ThreadLastVisit(models.Model):
    """ Entity which stores when a thread was last read. """
    user = models.ForeignKey(User)
    lastvisit = models.DateTimeField(default=datetime.now)
    thread = models.ForeignKey('Post')

    def __unicode__(self):
        return _("Last visit of '%(user)s' in thread '%(thread)s' at %(date)s") % \
                             {'user':self.user.get_full_name() or self.user.username,
                              'thread':self.thread.subject,
                              'date':self.lastvisit.strftime('%Y-%m-%d %H:%M:%S')}

    class Meta:
        verbose_name = ugettext_lazy('Thread last visit')
        verbose_name_plural = ugettext_lazy('Thread last visits')
        unique_together = (( "user", "thread", ),)


class CategoryLastVisit(models.Model):
    """ Entity which stores when a category was last accessed. """
    user = models.ForeignKey(User)
    lastvisit = models.DateTimeField(default=datetime.now)
    oldlastvisit = models.DateTimeField(null = True,)
    category = models.ForeignKey(Category)


    changelog = ( ( '2007-06-15 00', 'alter', 'ADD oldlastvisit timestamp with time zone' ),
                  )

    def __unicode__(self):
        return _("Last visit of '%(user)s' in category '%(category)s' at %(date)s") % \
                             {'user':self.user.get_full_name() or self.user.username,
                              'category':self.category.name,
                              'date':self.lastvisit.strftime('%Y-%m-%d')}

    class Meta:
        verbose_name = ugettext_lazy('Category last visit')
        verbose_name_plural = ugettext_lazy('Category last visits')
        unique_together = ('user', 'category')


class PostManager(models.Manager):
    """
    This custom manager makes sure that only visible posts are selected 
    (ie is_hidden has to be 0)
    """
    def get_query_set(self):
        return super(PostManager, self).get_query_set().filter(is_hidden = 0)


POST_STATUS_DEFAULT = 0
POST_STATUS_STICKY = 1
POST_STATUS_CLOSED = 2
POST_STATUS_POLL = 4
POST_STATUS_ANNOTATED = 8
POST_STATUS_NEW = 16

POST_STATUSES = {
    'default': 0,
    'sticky': 1,
    'closed': 2,

    'poll': 4,
    'annotated': 8,
    # the 'new' status is used in combination with the 'is_hidden'.
    # the first time a post is saved, the save() method sets this status if 'is_hidden'
    # is non-0 - the first time the save() method is called with is_hidden = 0 this status
    # is removed again (this is required to know when the Post is actually 'new' and email
    # notifications can be sent out).
    'new': 16,
    }


class Post(models.Model):
    """
    A Post object can either represent a new thread (in this case 
    thread is None and there exists a ThreadInformation model) or a reply within a thread.

    if anything has to be done when a new post is created it is important to make sure that
    'is_hidden' is 0 - if it is non-0 it is not really created right now.
    """
    status = models.IntegerField(default = 0, editable = False )
    category = models.ForeignKey(Category, related_name = 'posts', editable = False )
    subject = models.CharField(max_length = 250)
    body = models.TextField()
    thread = models.ForeignKey('self', null = True, editable = False )
    postdate = models.DateTimeField( auto_now_add = True, editable = False )
    author = models.ForeignKey(User, editable = False, null = True, blank = True, related_name = 'sphboard_post_author_set' )
    markup = models.CharField(max_length = 250,
                              null = True,
                              choices = POST_MARKUP_CHOICES, )
    # is_hidden allows basic CMS functionality as well as uploads to posts because
    # basically you can create a Post object without any influence..
    # (if something is hidden, it is ALWAYS hidden, not even shown to an administrator.
    #  a custom category type might change this behavior tough by adding a 
    #  administration interface for hidden posts.)
    is_hidden = models.IntegerField(default = 0, editable = False, db_index = True )

    # allobjects also contain hidden posts.
    allobjects = models.Manager()
    # objects only contains non-hidden posts.
    objects = PostManager()

    changelog = ( ( '2007-04-07 00', 'alter', 'ALTER author_id DROP NOT NULL', ),
                  ( '2007-06-16 00', 'alter', 'ADD markup varchar(250) NULL', ),
                  ( '2008-01-06 00', 'alter', 'ADD is_hidden INTEGER', ),
                  ( '2008-01-06 01', 'update', 'SET is_hidden = 0', ),
                  ( '2008-01-06 02', 'alter', 'ALTER is_hidden SET NOT NULL', ),
                  )

    def is_sticky(self):
        return self.status & POST_STATUS_STICKY
    def is_closed(self):
        return self.status & POST_STATUS_CLOSED
    def is_poll(self):
        return self.status & POST_STATUS_POLL
    def is_annotated(self):
        return self.status & POST_STATUS_ANNOTATED
    def is_new(self):
        return self.status & POST_STATUS_NEW

    def set_sticky(self, sticky):
        if sticky: self.status = self.status | POST_STATUS_STICKY
        else: self.status = self.status ^ POST_STATUS_STICKY

    def set_closed(self, closed):
        if closed: self.status = self.status | POST_STATUS_CLOSED
        else: self.status = self.status ^ POST_STATUS_CLOSED

    def set_poll(self, poll):
        if poll: self.status = self.status | POST_STATUS_POLL
        else: self.status = self.status ^ POST_STATUS_POLL

    def set_annotated(self, annotated):
        if annotated: self.status = self.status | POST_STATUS_ANNOTATED
        else: self.status = self.status ^ POST_STATUS_ANNOTATED

    def set_new(self, new):
        if new: self.status = self.status | POST_STATUS_NEW
        else: self.status = self.status ^ POST_STATUS_NEW

    def get_thread(self):
        if self.thread == None: return self;
        return self.thread;

    def get_threadinformation(self):
        return ThreadInformation.objects.type_default().get( root_post = self.get_thread() )

    def get_all_posts(self):
        return Post.objects.filter( Q( pk = self.id ) | Q( thread = self ) )

    def replies(self):
        return Post.objects.filter( thread = self )

    def _cache_key_post_count(self):
        return '%s_thread_post_count_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.thread_id or self.pk)

    def postCount(self):
        res = cache.get(self._cache_key_post_count())
        if not res:
            res = self.get_all_posts().count()
            cache.set(self._cache_key_post_count(), res)
        return res

    def replyCount(self):
        return self.postCount() - 1

    def allow_posting(self, user):
        """
        Returns True if the user is allowed to post replies in this thread.

        if user is None, the current user is taken into account.
        """
        return not self.is_closed() and \
               ( self.category.testAllowance( user, self.category.allowreplies ) \
                 or has_permission_flag( user, 'sphboard_post_replies', self.category ) )
    allowPosting = allow_posting

    def allow_editing(self, user = None):
        """
        Returns True if the user is allowed to edit this post.

        if user is None, the current user is taken into account.
        """
        if user == None: user = get_current_user()
        
        if not user or not user.is_authenticated():
            # Quick hack to make anonymous uploading of attachments possible
            if self.is_hidden != 0 and self.is_new():
                return True
            return False
        
        if user.is_superuser \
               or has_permission_flag( user, 'sphboard_editallposts', self.category ):
            return True

        if user == self.author:
            # Check edit timeout
            remaining = self.remaining_edit_seconds(user)
            if remaining == -1 or remaining > 0:
                return True

        return False

    def remaining_edit_seconds(self, user = None):
        """
        Returns the number of seconds the user is allowed to edit the post
        returns -1 for unlimited (Not checking user permissions !!)
        """
        if user is None: user = get_current_user()
        
        timeout = get_sph_setting( 'board_edit_timeout' )

        if timeout < 0:
            return timeout

        delta = (timezone.now() - self.postdate)
        totalseconds = delta.days * 24 * 60 * 60 + delta.seconds

        if timeout >= totalseconds:
            return timeout - totalseconds

        # Timed out ....
        return 0

    allowEditing = allow_editing

    def allow_hiding(self, user = None):
        """
        Returns True if the user is allowed to hide (set is_hidden=True) this post.

        if user is None, the current user is taken into account.
        """
        if user == None: user = get_current_user()

        if not user or not user.is_authenticated():
            return False

        if user.is_superuser \
               or has_permission_flag( user, 'sphboard_hideallposts', self.category ):
            return True

        if user == self.author:
            # Check edit timeout
            remaining = self.remaining_hide_seconds(user)
            if remaining == -1 or remaining > 0:
                # if there are newer posts (that may have quoted current post)
                # don't allow to hide post
                if self.thread_has_newer_posts():
                    return False
                return True

        return False

    def thread_has_newer_posts(self, post):
        """
        Check if there are posts newer than 'post'
        """
        if post.pk == self.latest().pk:
            return True
        return False

    def remaining_hide_seconds(self, user = None):
        """
        Returns the number of seconds the user is allowed to hide the post
        returns -1 for unlimited (Not checking user permissions !!)
        """
        if user is None: user = get_current_user()

        timeout = get_sph_setting( 'board_hide_timeout' )

        if timeout < 0:
            return timeout

        delta = (timezone.now() - self.postdate)
        totalseconds = delta.days * 24 * 60 * 60 + delta.seconds

        if timeout >= totalseconds:
            return timeout - totalseconds

        # Timed out ....
        return 0
    allowHiding = allow_hiding

    def _allow_adminfunctionality(self, flag, user = None):
        if user == None:
            user = get_current_user()

        if not user or not user.is_authenticated():
            return False

        return user.is_staff or has_permission_flag( user, flag, self.category )

    def allow_moving_post(self, user = None):
        """
        Returns True if the user is allowed to move the post
        """
        return self._allow_adminfunctionality( 'sphboard_moveallposts', user )
    allowMovingPost = allow_moving_post

    def allow_annotating(self, user = None):
        """
        Returns True if the user is allowed to annotate this post.

        if user is None, the current user is taken into account.
        """
        return self._allow_adminfunctionality( 'sphboard_annotate', user )

    def allow_moving(self, user = None):
        return self._allow_adminfunctionality( 'sphboard_move', user )

    def allow_locking(self, user = None):
        return self._allow_adminfunctionality( 'sphboard_lock', user )
    
    def allow_sticking(self, user = None):
        return self._allow_adminfunctionality( 'sphboard_sticky', user )

    def __get_render_cachekey(self):
        return '%s-sphboard_rendered_body_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, str(self.id))

    def body_escaped(self, with_signature = True):
        """ returns the rendered body. """
        body = self.body
        markup = self.markup
        if not markup:
            markup = POST_MARKUP_CHOICES[0][0]

        # Check cache
        bodyhtml = None
        cachekey = None
        if self.id:
            cachekey = self.__get_render_cachekey()
            bodyhtml = cache.get( cachekey )
        if bodyhtml is None:
            # Nothing found in cache, render body.
            bodyhtml = render_body( body, markup )
            if cachekey is not None:
                cache.set( cachekey, bodyhtml, get_sph_setting( 'board_body_cache_timeout' ) )

        if self.author_id and with_signature:
            signature = get_rendered_signature( self.author_id )
            if signature:
                board_signature_tag = get_sph_setting('board_signature_tag')
                bodyhtml += board_signature_tag % {'signature':signature}
        return mark_safe(bodyhtml)

    def body_rendered_without_signature(self):
        return self.body_escaped(with_signature = False)

    def clear_render_cache(self):
        cache.delete( self.__get_render_cachekey() )

    def viewed(self, session, user):
        if get_sph_setting( 'board_count_views' ):
            threadinfo = self.get_threadinformation()
            threadinfo.view_count += 1
            threadinfo.save()
        self.touch(session, user)

    def touch(self, session, user):
        return self._touch( session, user )

    def _touch(self, session, user):
        if not user.is_authenticated(): return None
        category_lastvisit = self.category.touch(session, user)
        if not self._hasNewPosts(session, user): return None

        # Check all posts to see if they are new
        # Check if current user has any unread threads and if he doesn't
        # then remove all treheadlastvisit objects - this means that every thread was last visited when
        # category was last visited
        thread = self.thread or self

        thread_last_visit, created = ThreadLastVisit.objects.get_or_create(user=user,
                                                                           thread=thread)
        if not created:
            thread_last_visit.lastvisit = timezone.now()
            thread_last_visit.save()

        self.category.update_unread_status(user)
        return False


    def has_new_posts(self):
        if hasattr(self, '__has_new_posts'): return self.__has_new_posts
        self.__has_new_posts = self._hasNewPosts(get_current_session(), get_current_user())
        return self.__has_new_posts

    def _cache_key_latest_post(self):
        return '%s_post_lp_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, self.pk)

    def get_latest_post(self):
        key = self._cache_key_latest_post()
        res = cache.get(key)
        if not res:
            try:
                res = self.get_all_posts().latest( 'postdate' )
                cache.set(key, res)
            except Post.DoesNotExist:
                cache.set(key, None)
        return res
    
    def _hasNewPosts(self, session, user):
        if not user.is_authenticated(): return False
        latestPost = self.get_latest_post()
        categoryLastVisit = self.category.get_lastvisit_date(user)
        if categoryLastVisit > latestPost.postdate:
            return False

        try:
            threadLastVisit = ThreadLastVisit.objects.filter( user = user,
                                                              thread__id = self.id, )[0]
            return threadLastVisit.lastvisit < latestPost.postdate
        except IndexError:
            return True


    def poll(self):
        try:
            return self.poll_set.get()
        except Poll.DoesNotExist:
            return None

    def has_monitor(self):
        """Returns True if there is a monitor for the current user in this
        thread. (Will also return True if there is a monitor in a category !)
        To check this, call has_direct_monitor !
        """
        monitor = self.__get_monitor(get_current_user())
        if monitor: return True
        return False

    def has_direct_monitor(self):
        """Return only True if there is a direct monitor for THIS thread."""
        monitor = self.__get_monitor(get_current_user())
        thread = self.thread or self
        return monitor and monitor.thread == thread

    def __get_monitor(self, user):
        if hasattr(self, '__monitor'): return self.__monitor
        thread = self.thread or self
        try:
            monitor = Monitor.objects.get( thread = thread,
                                           user = user, )
        except Monitor.DoesNotExist:
            monitor = thread.category.has_monitor()
        self.__monitor = monitor
        return self.__monitor

    def toggle_monitor(self, user=None):
        if not user:
            user = get_current_user()
        if self.has_direct_monitor():
            self.__get_monitor(user).delete()
            if hasattr(self, '__monitor'): delattr(self,'__monitor')
        else:
            thread = self.thread or self
            monitor = Monitor( thread = thread,
                               category = thread.category,
                               group = thread.category.group,
                               user = user, )
            monitor.save()
            self.__monitor = monitor
            return monitor

    def hide(self):
        """ Hide (delete) the post. If post is root post of the thread then hide all posts below it too
        """
        thread = self.get_thread()
        is_root_post = thread.pk == self.pk

        # if removed post is root post of thread
        if is_root_post:
            Post.objects.filter(thread = self).update(is_hidden = 1)
        self.is_hidden = 1
        self.save()

    def save(self, force_insert=False, force_update=False, additional_data=None):
        isnew = not self.id

        if isnew and self.is_hidden != 0:
            self.set_new( True )
            isnew = False
        elif not isnew and self.is_new() and self.is_hidden == 0:
            self.set_new( False)
            isnew = True

        # set a 'is_new_post' attribute which can be checked by post_save
        # signal handler if this is really a new post (to send out email notifications
        # or similar)
        self.is_new_post = isnew
        ret = super(Post, self).save(force_insert=force_insert, force_update=force_update)

        if additional_data is not None:
            self.category.get_category_type().save_post(self, additional_data)

        # Clear cache
        cache.delete( self.__get_render_cachekey() )
        if isnew:
            if not hasattr(settings, 'SPH_SETTINGS') or \
                   not 'noemailnotifications' in settings.SPH_SETTINGS or \
                   not settings.SPH_SETTINGS['noemailnotifications']:
                # Email Notifications ....
                thread = self.thread or self
                # thread monitors ..
                allmonitors = Monitor.objects.all()
                monitors = allmonitors.filter( thread = thread )
                # any category monitors
                category = self.category
                while category:
                    monitors = monitors | allmonitors.filter( category = category, thread__isnull = True )
                    category = category.parent
                    # group monitors
                    monitors = monitors | allmonitors.filter( group = self.category.group, category__isnull = True, thread__isnull = True )
                    #monitors = Monitor.objects.filter(myQ)
                    
                subject = _('New Forum Post in "%(category_name)s": %(subject)s') % {'category_name':self.category.name,
                                                                                     'subject':self.subject}
                group = get_current_group() or self.category.group
                t = loader.get_template('sphene/sphboard/new_post_email.txt')
                c = {
                    'baseurl': group.baseurl,
                    'group': group,
                    'post': self,
                    }
                body = t.render(RequestContext(get_current_request(), c))
                #body = ("%s just posted in a thread or forum you are monitoring: \n" + \
                #        "Visit http://%s/%s") % (group.baseurl, self.author.get_full_name(), self.get_absolute_url())
                datatuple = ()
                sent_email_addresses = ()
                if self.author != None:
                    sent_email_addresses += (self.author.email,) # Exclude the author of the post
                logger.debug('Finding email notification monitors ..')
                for monitor in monitors:
                    if monitor.user.email in sent_email_addresses : continue
                    if monitor.user.email == '': continue

                    # Check Permissions ...
                    if not self.category.has_view_permission( monitor.user ):
                        logger.info( "User {%s} has monitor but no view permission for category {%s}" % (str(monitor.user),
                                                                                                         str(self.category),))
                        continue

                    logger.info( "Adding user {%s} email address to notification email." % str(monitor.user) )
                
                    # Add email address to address tuple ...
                    datatuple += (subject, body, None, [monitor.user.email,]),
                    sent_email_addresses += monitor.user.email,

                logger.info( "Sending email notifications - {%s}" % str(datatuple) )
                if datatuple:
                    send_mass_mail(datatuple, )
        
        return ret

    def __unicode__(self):
        return self.subject

    def get_page(self):
        if self.thread is None:
            return 1
        threadinfo = self.get_threadinformation()
        if threadinfo.latest_post == self:
            return threadinfo.get_page_count()

        i = 0
        for post in self.thread.get_all_posts():
            i+=1
            if post == self:
                break
        import math
        return int(math.ceil(i / float(get_sph_setting( 'board_post_paging' ))))

    def _cache_key_absolute_url(self):
        return '%s_post_abs_url_%s_%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX,
                                             self.pk,
                                             get_sph_setting('board_slugify_links'),
                                             get_sph_setting( 'board_post_paging' ))

    def get_absolute_url(self):
        key = self._cache_key_absolute_url()
        res = cache.get(key)
        if not res:
            cturl = self.category.get_category_type().get_absolute_url_for_post( self )
            if cturl:
                res = cturl
            else:
                res = "%s?page=%d#post-%d" % (self._get_absolute_url(),
                                              self.get_page(),
                                              self.id)
            cache.set(key, res)
        return res

    def _get_absolute_url(self):
        kwargs = { 'groupName': self.category.group.name,
                   'thread_id': self.thread and self.thread.id or self.id }
        if get_sph_setting('board_slugify_links'):
            name = 'sphboard_show_thread'
            kwargs['slug'] = slugify(self.get_thread().subject) or '_'
        else:
            name = 'sphboard_show_thread_without_slug'
        return (name, (), kwargs)
    _get_absolute_url = sphpermalink(_get_absolute_url)
    
    def get_absolute_editurl(self):
        return ('sphene.sphboard.views.post', (), { 'groupName': self.category.group.name, 'category_id': self.category.id, 'post_id': self.id })
    get_absolute_editurl = sphpermalink(get_absolute_editurl)

    def get_absolute_hideurl(self):
        return ('sphene.sphboard.views.hide', (), { 'groupName': self.category.group.name, 'post_id': self.id })
    get_absolute_hideurl = sphpermalink(get_absolute_hideurl)

    def get_absolute_moveposturl(self):
        return ('sphene.sphboard.views.move_post_1', (), { 'groupName': self.category.group.name, 'post_id': self.id })
    get_absolute_moveposturl = sphpermalink(get_absolute_moveposturl)

    def get_absolute_postreplyurl(self):
        return ('sphene.sphboard.views.reply', (), { 'groupName': self.category.group.name, 'category_id': self.category.id, 'thread_id': self.get_thread().id })
    get_absolute_postreplyurl = sphpermalink(get_absolute_postreplyurl)

    def get_absolute_annotate_url(self):
        return ('sphene.sphboard.views.annotate', (), { 'groupName': self.category.group.name, 'post_id': self.id })
    get_absolute_annotate_url = sphpermalink(get_absolute_annotate_url)

    def get_absolute_lastvisit_url(self):
        user = get_current_user()
        session = get_current_session()
        # not authenticated users always see first post in thread
        new_post = self
        if user.is_authenticated():
            # for authenticated users
            latest_post = self.get_latest_post()
            categoryLastVisit = self.category.get_lastvisit_date(user)
            if categoryLastVisit > latest_post.postdate:
                # no new posts in thread - return latest post
                new_post = latest_post
            else:
                try:
                    threadLastVisit = ThreadLastVisit.objects.filter(user=user,
                                                                     thread__id=self.id)[0]
                    new_posts = self.replies().filter(postdate__gt=threadLastVisit.lastvisit)
                    if new_posts.count()>0:
                        # return first post added after last visit
                        new_post = new_posts[0]
                    else:
                        # no new posts so return latest post
                        new_post = latest_post
                except IndexError:
                    # whole thread not seen, show first post
                    new_post = self
        return new_post.get_absolute_url()
    
    class Meta:
        verbose_name = ugettext_lazy('Post')
        verbose_name_plural = ugettext_lazy('Posts')

class PostAttachment(models.Model):
    post = models.ForeignKey(Post, related_name = 'attachments')
    # This is only blank so the form does not throw errors when it was not entered !
    fileupload = models.FileField( ugettext_lazy(u'File'),
                                   upload_to = get_sph_setting( 'board_attachments_upload_to' ),
                                   blank = True )

    def is_image(self):
        (type, encoding) = mimetypes.guess_type(self.fileupload.name)
        if type is None:
            return False
        return type.startswith('image/')

    class Meta:
        verbose_name = ugettext_lazy('Post attachment')
        verbose_name_plural = ugettext_lazy('Post attachments')


class PostAnnotation(models.Model):
    """
    Represents an admin annotation to a post - for example to hide
    a post if it violates the rules.
    It is also used as comment field when a thread is moved into
    another category.
    """

    # Only one annotation per post allowed !
    post = models.ForeignKey(Post, related_name = 'annotation', unique = True, )
    body = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField( )
    hide_post = models.BooleanField()
    markup = models.CharField(max_length = 250,
                              null = True,
                              choices = POST_MARKUP_CHOICES, )

    def save(self, force_insert=False, force_update=False):
        if not self.post.is_annotated():
            self.post.set_annotated(True)
            self.post.save()
        if not self.created:
            self.created = timezone.now()
        if not self.id:
            self.author = get_current_user()
        return super(PostAnnotation, self).save(force_insert=force_insert, force_update=force_update)

    def body_escaped(self):
        body = self.body
        markup = self.markup
        if not markup:
            markup = POST_MARKUP_CHOICES[0][0]
        return mark_safe( render_body( body, markup ) )

    class Meta:
        verbose_name = ugettext_lazy('Post annotation')
        verbose_name_plural = ugettext_lazy('Post annotations')

THREAD_TYPE_DEFAULT = 1
THREAD_TYPE_MOVED = 2

thread_types = (
    (THREAD_TYPE_DEFAULT, 'Default'),
    (THREAD_TYPE_MOVED  , 'Moved Thread'),
    )


class ThreadInformationManager(models.Manager):
    def type_default(self):
        return self.filter( thread_type = THREAD_TYPE_DEFAULT )


class ThreadInformation(models.Model):
    """ A object which holds information about threads and caches
    a couple of things which are redundant. """
    root_post = models.ForeignKey( Post, null = False, blank = False )
    category = models.ForeignKey( Category )

    # A thread type allows the decleration of a "Moved" thread.
    thread_type = models.IntegerField( choices = thread_types )

    # the "heat" value between -100 and 100 where >0 represents a "hot" thread.
    heat = models.IntegerField( default = 0, db_index = True )
    heat_calculated = models.DateTimeField( null = True )

    # For performance reasons store latest posts and various counters here ..
    sticky_value = models.IntegerField( default = 0, db_index = True )
    latest_post = models.ForeignKey( Post, related_name = 'thread_latest_set' )
    post_count = models.IntegerField( default = 0 )
    view_count = models.IntegerField( default = 0 )
    # To make it even easier / faster to order by the latest post date..
    thread_latest_postdate = models.DateTimeField( db_index = True )

    objects = ThreadInformationManager()


    def save(self, force_insert=False, force_update=False):
        if self.thread_latest_postdate is None:
            self.thread_latest_postdate = self.latest_post.postdate
        
        super(ThreadInformation, self).save(force_insert=force_insert, force_update=force_update)

    def is_hot(self):
        if self.heat_calculated and (timezone.now() - self.heat_calculated).days > 7:
            logger.debug( 'Heat was not calculated in the last 7 days - recalculating...' )
            self.update_heat()
            self.save()
            
        """ Returns True if this thread represents a "Hot" topic.
        If it returns True you can look for the 'heat' property for the exact value. """
        return self.heat > 0

    def update_cache(self):
        """ Will update the latest_post and post_count of this model.
        (Ie. the cache - or redundant information.)
        Does not save this model ! This has to be done by the caller. """
        # clear caches
        cache.delete(self.root_post._cache_key_post_count())
        cache.delete(self.root_post._cache_key_latest_post())

        # Find sticky ..
        self.sticky_value = self.root_post.is_sticky() and 1 or 0
        # Find the last post ...
        latest = self.root_post.get_latest_post()
        if latest:
            self.latest_post = latest
        self.thread_latest_postdate = self.latest_post.postdate
        # Calculate post count ...
        self.post_count = self.root_post.postCount()
        self.update_heat()

    def update_heat(self):
        """
        Updates the heat value - this should be run periodically.
        Or at least every time a post is added to a thread.
        
        The caller has to ensure that the thread is saved afterwards !
        """
        days = get_sph_setting( 'board_heat_days' )

        # Get the number of posts of the last x days
        count = self.root_post.get_all_posts().filter( postdate__gte = timezone.now() - timedelta( days ) ).count()
        views = self.view_count

        age = -(self.root_post.postdate - timezone.now()).days

        heat_calculator = get_method_by_name( get_sph_setting( 'board_heat_calculator' ) )
        heat = heat_calculator( thread = self,
                                postcount = count,
                                viewcount = views,
                                age = age, )
        logger.debug( "Number of posts in the last %d days: %d - age: %d - views: %d - resulting heat: %d" % (days, count, age, views, heat) )
        self.heat = int(heat)
        self.heat_calculated = timezone.now()
        
    def is_sticky(self):
        return self.sticky_value > 0

    def is_moved(self):
        """ Returns true if this thread represents a thread which was moved
        into another category. """
        return self.thread_type == THREAD_TYPE_MOVED

    def get_page_count(self):
        """ Returns the number of pages this thread has. """
        import math
        # No idea why ceil wouldn't return a integer value ..
        return int(math.ceil(self.root_post.postCount() / float(get_sph_setting( 'board_post_paging' ))))

    def has_paging(self):
        return self.root_post.postCount() > get_sph_setting( 'board_post_paging' )

    #################################
    ## Some proxy methods which will simply forward
    ## the calls to the root post.

    def author(self):
        return self.root_post.author

    def subject(self):
        return self.root_post.subject

    def is_poll(self):
        return self.root_post.is_poll()

    def is_closed(self):
        return self.root_post.is_closed()

    def has_new_posts(self):
        return self.root_post.has_new_posts()

    ##
    ###################################

    def get_threadlist_subject(self):
        return self.category.get_category_type().get_threadlist_subject( self )

    def get_absolute_url(self):
        cturl = self.category.get_category_type().get_absolute_url_for_post( self.root_post )
        if cturl:
            return cturl
        #return self._get_absolute_url()
        return self.root_post.get_absolute_url()

    def get_absolute_url_nopaging(self):
        cturl = self.category.get_category_type().get_absolute_url_for_post( self.root_post )
        if cturl:
            return cturl
        return self._get_absolute_url()

    def get_absolute_lastvisit_url(self):
        return self.root_post.get_absolute_lastvisit_url()

    def allow_deleting_moved(self, user = None):
        """
        Returns True if the user is allowed to delete thread information about moved thread.

        if user is None, the current user is taken into account.
        """
        if user == None: user = get_current_user()

        if not user or not user.is_authenticated() or self.thread_type != THREAD_TYPE_MOVED:
            return False

        if user.is_superuser \
               or has_permission_flag( user, 'sphboard_delete_moved_threadinformation', self.category ):
            return True

        return False

    def _get_absolute_url(self):
        kwargs = { 'groupName': self.category.group.name,
                   'thread_id': self.root_post.id }
        name = 'sphboard_show_thread_without_slug'
        if get_sph_setting('board_slugify_links'):
            slug = slugify(self.root_post.subject)
            if slug:
                name = 'sphboard_show_thread'
                kwargs['slug'] = slug
        return (name, (), kwargs)
    _get_absolute_url = sphpermalink(_get_absolute_url)

    def __unicode__(self):
        return self.root_post.subject

    class Meta:
        verbose_name = ugettext_lazy('Thread information')
        verbose_name_plural = ugettext_lazy('Thread informations')

def calculate_heat(thread, postcount, viewcount, age):
    """
    This method can be customized by setting board_heat_calculator to your own
    method which will replace this one.

    It should return the "heat" (Usually something between -100 and 100 - where >0 should represent
    a "hot" thread.
    """

    post_threshold = get_sph_setting( 'board_heat_post_threshold' )
    view_threshold = get_sph_setting( 'board_heat_view_threshold' )

    # It is enough to fulfill one threshold to make a hot thread.
    postheat = 0
    viewheat = 0
    if postcount > 0:
        postheat = (100. / post_threshold * postcount)
    if viewcount > 0:
        viewheat = (100. / view_threshold * (float(viewcount)/age))

    # Subtract 100 to have non-hot topic <0
    heat = (postheat + viewheat) - 100

    return heat

def update_heat(**kwargs):
    """
    This method should be regularly called through a cronjob or similar -
    this can be done by simply dispatching the maintenance signal.

    see sphenecoll/sphene/community/signals.py for more details.
    """
    all_threads = ThreadInformation.objects.all()
    for thread in all_threads:
        thread.update_heat()
        thread.save()

sphene.community.signals.maintenance.connect(update_heat)

def update_thread_information(instance, **kwargs):
    """
    Updates the thread information every time a post is saved.
    """
    thread = instance.get_thread()
    threadinfos = ThreadInformation.objects.filter( root_post = thread )
    
    if len(threadinfos) < 1:
        if thread.is_hidden != 0:
            # If thread is still hidden, don't bother creating a 
            # ThreadInformation object.
            return
        threadinfos = ( ThreadInformation( root_post = thread,
                                           category = thread.category,
                                           thread_type = THREAD_TYPE_DEFAULT, ),  )
    for threadinfo in threadinfos:
        threadinfo.update_cache()
        threadinfo.save()

signals.post_save.connect(update_thread_information,
                   sender = Post)

def ensure_thread_information():
    """
    Iterates through all threads and verifies that there is a corresponding
    ThreadInformation object. (Useful for updates)
    """
    allthreads = Post.objects.filter( thread__isnull = True )
    print "Validating Thread information ..."
    for thread in allthreads:
        update_thread_information( thread )
    print "Done."


class Monitor(models.Model):
    """Monitors allow user to get notified by email on new posts in a
    particular thread, category or a whole board of a group."""
    
    thread = models.ForeignKey(Post, null = True, blank = True)
    category = models.ForeignKey(Category, null = True, blank = True)
    group = models.ForeignKey(Group)
    user = models.ForeignKey(User)

    class Meta:
        verbose_name = ugettext_lazy('Monitor')
        verbose_name_plural = ugettext_lazy('Monitors')


class Poll(models.Model):
    post = models.ForeignKey(Post, editable = False)
    question = models.CharField( max_length = 250 )
    choices_per_user = models.IntegerField( )

    def multiplechoice(self):
        return self.choices_per_user != 1

    def choices(self):
        return self.pollchoice_set.all()

    def has_voted(self, user = None):
        if not user: user = get_current_user()
        if not user.is_authenticated(): return False
        return self.pollvoters_set.filter( user = user ).count() > 0

    def total_voters(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT user_id) as totalvoters FROM sphboard_pollvoters WHERE poll_id = %s", [self.id])
        row = cursor.fetchone()
        return row[0]

    def total_votes(self):
        return self.pollvoters_set.count()

    def null_votes(self):
        return self.pollvoters_set.filter( choice__isnull = True ).count()

    def allow_editing(self, user = None):
        return self.post.allow_editing(user)

    def get_absolute_editurl(self):
        return ('sphboard_edit_poll', (), { 'poll_id': self.id, })
    get_absolute_editurl = sphpermalink(get_absolute_editurl)

    class Meta:
        verbose_name = ugettext_lazy('Poll')
        verbose_name_plural = ugettext_lazy('Polls')


class PollChoice(models.Model):
    poll = models.ForeignKey(Poll, editable = False)
    choice = models.CharField( max_length = 250 )
    count = models.IntegerField()
    sortorder = models.IntegerField( default = 0, null = False )

    changelog = ( ( '2008-03-14 00', 'alter', 'ADD sortorder INTEGER' ),
                  ( '2008-03-14 01', 'update', 'SET sortorder = 0' ),
                  ( '2008-03-14 02', 'alter', 'ALTER sortorder SET NOT NULL' ),
                  )

    class Meta:
        verbose_name = ugettext_lazy('Poll choice')
        verbose_name_plural = ugettext_lazy('Poll choices')
        ordering = [ 'sortorder' ]


class PollVoters(models.Model):
    poll = models.ForeignKey(Poll, editable = False)
    choice = models.ForeignKey(PollChoice, null = True, blank = True, editable = False)
    user = models.ForeignKey(User, editable = False)

    class Meta:
        verbose_name = ugettext_lazy('Poll voter')
        verbose_name_plural = ugettext_lazy('Poll voters')


class BoardUserProfile(models.Model):
    user = models.ForeignKey( User, unique = True)
    signature = models.TextField(ugettext_lazy(u'Signature'), default = '')
    
    markup = models.CharField(ugettext_lazy(u'Markup'), max_length = 250,
                              null = True,
                              choices = POST_MARKUP_CHOICES, )

    default_notifyme_value = models.NullBooleanField(null = True, )

    def render_signature(self):
        if self.signature == '':
            return ''
        return render_body(self.signature, self.markup)

    class Meta:
        verbose_name = ugettext_lazy('Board user profile')
        verbose_name_plural = ugettext_lazy('Board user profiles')


class UserPostCountManager(models.Manager):
    def get_post_count(self, user, group):
        if user is None:
            return None
        try:
            return self.get(user = user, group = group ).post_count
        except UserPostCount.DoesNotExist:
            return self.update_post_count(user, group)

    def update_post_count(self, user, group):
        if user is None:
            return None
        upc, created = UserPostCount.objects.get_or_create(user = user, group = group)
        upc.update_post_count()
        upc.save()
        return upc.post_count


class UserPostCount(models.Model):
    user = models.ForeignKey( User )
    group = models.ForeignKey( Group, null=True )
    post_count = models.IntegerField(default=0)

    objects = UserPostCountManager()

    def update_post_count(self):
        qry = self.user.sphboard_post_author_set
        try:
            qry = qry.filter(category__group = self.group)
        except:
            qry = qry.filter(category__group__isnull = True)
        qry = qry.filter(is_hidden=0)
        
        self.post_count = qry.count()

    class Meta:
        verbose_name = ugettext_lazy('User post count')
        verbose_name_plural = ugettext_lazy('User post counts')
        unique_together = ( 'user', 'group' )


def update_post_count(instance, **kwargs):
    UserPostCount.objects.update_post_count( instance.author, instance.category.group )

signals.post_save.connect(update_post_count,
                   sender = Post)


class ExtendedCategoryConfig(models.Model):
    category = models.ForeignKey( Category, unique = True )

    subject_label = models.CharField( max_length = 250, blank = True )
    body_label = models.CharField( max_length = 250, blank = True )
    body_initial = models.TextField(blank = True)
    body_help_text = models.TextField(blank = True)
    
    post_new_thread_label = models.CharField( max_length = 250, blank = True)
    above_thread_list_block = models.TextField(blank = True, help_text = 'HTML which will be displayed above the thread list.')

    class Meta:
        verbose_name = ugettext_lazy('Extended category config')
        verbose_name_plural = ugettext_lazy('Extended category configs')


def __get_signature_cachekey(user_id):
    return '%s_sphboard_signature_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, user_id)

def get_rendered_signature(user_id):
    """ Returns the rendered signature for the given user. """
    # TODO add caching !
    cachekey = __get_signature_cachekey(user_id)
    rendered_profile = cache.get( cachekey )
    if rendered_profile is not None:
        return rendered_profile
    
    try:
        profile = BoardUserProfile.objects.get( user__pk = user_id, )
        
        rendered_profile = profile.render_signature()
    except BoardUserProfile.DoesNotExist:
        rendered_profile = ''

    cache.set( cachekey, rendered_profile, get_sph_setting( 'board_signature_cache_timeout' ) )
    
    return rendered_profile

def clear_signature_cache(instance, **kwargs):
    cache.delete( __get_signature_cachekey( instance.user.id ) )


signals.post_save.connect(clear_signature_cache,
                   sender = BoardUserProfile)


def board_profile_edit_init_form(sender, instance, signal, *args, **kwargs):
    user = instance.user
    try:
        profile = BoardUserProfile.objects.get( user = user, )
    except:
        profile = BoardUserProfile( user = user )

    instance.fields['board_settings'] = Separator(label=_(u'Board settings'))
    instance.fields['signature'] = forms.CharField(label=_(u'Signature'), 
                                                   widget = forms.Textarea( attrs = { 'rows': 3, 'cols': 40 } ),
                                                   required = False,
                                                   initial = profile.signature, )
    if len( POST_MARKUP_CHOICES ) != 1:
        instance.fields['markup'] = forms.CharField(widget = forms.Select( choices = POST_MARKUP_CHOICES, ),
                                                    required = False,
                                                    initial = profile.markup, )
    instance.fields['default_notifyme_value'] = forms.NullBooleanField( label = _(u'Default Notify Me - Value'),
                                                                        required = False,
                                                                        initial = profile.default_notifyme_value, )

def board_profile_edit_save_form(sender, instance, signal, request, **kwargs):
    user = instance.user
    data = instance.cleaned_data
    try:
        profile = BoardUserProfile.objects.get( user = user, )
    except BoardUserProfile.DoesNotExist:
        profile = BoardUserProfile( user = user )

    profile.signature = data['signature']
    if len( POST_MARKUP_CHOICES ) != 1:
        profile.markup = data['markup']
    else:
        profile.markup = POST_MARKUP_CHOICES[0][0]
    profile.default_notifyme_value = data['default_notifyme_value']

    profile.save()
    messages.success(request,  message = _(u"Successfully saved board profile.") )

def board_profile_display(sender, signal, request, user, **kwargs):
    ret = '<tr><th>%s</th><td>%d</td></tr>' % (
            _('Posts'), UserPostCount.objects.get_post_count(user, get_current_group()), )
    try:
        profile = BoardUserProfile.objects.get( user = user, )

        if profile.signature:
            ret += '<tr><th colspan="2">%s</th></tr><tr><td colspan="2">%s</td></tr>' % (
                _('Board Signature'), profile.render_signature(), )

    except BoardUserProfile.DoesNotExist:
        pass

    from sphene.sphboard.views import render_latest_posts_of_user
    blocks = '<div>%s</div>' % render_latest_posts_of_user(request, get_current_group(), user)
    return { 'additionalprofile': ret,
             'block': mark_safe(blocks), }

profile_edit_init_form.connect(board_profile_edit_init_form, sender = EditProfileForm)
profile_edit_save_form.connect(board_profile_edit_save_form, sender = EditProfileForm)
profile_display.connect(board_profile_display)
signals.post_save.connect(clear_category_cache, sender=Group)
signals.post_save.connect(clear_category_cache, sender=Category)
signals.pre_save.connect(clear_post_cache, sender=Post)
signals.pre_save.connect(clear_post_cache, sender=Group)
signals.pre_save.connect(clear_post_cache, sender=Category)
signals.post_delete.connect(clear_post_cache_on_delete, sender=Post)
signals.pre_save.connect(clear_post_4_category_cache, sender=Post)
signals.pre_save.connect(mark_thread_moved_deleted, sender=Post)
signals.post_save.connect(clear_category_unread_after_post_move, sender=Post)
signals.post_save.connect(update_category_last_visit_cache, sender=CategoryLastVisit)
