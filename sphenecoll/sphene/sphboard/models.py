from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from sphene.community.permissionutils import has_permission_flag
from sphene.community.models import Group, Role, PermissionFlag, RoleMember

from django.utils import html
from django.conf import settings
from datetime import datetime, timedelta

#from django.db.models import permalink
from django.dispatch import dispatcher
from django.db.models import signals
from sphene.community.sphutils import sphpermalink as permalink, get_urlconf, get_sph_setting, get_method_by_name
import sphene.community.signals
from django.core import exceptions
from django.core.urlresolvers import reverse
from django.core.mail import send_mass_mail
from django.template.context import RequestContext
from django.template import loader, Context
from django.core.cache import cache
from sphene.community.middleware import get_current_request, get_current_user, get_current_group, get_current_session
from renderers import POST_MARKUP_CHOICES, render_body
import logging

logger = logging.getLogger('sphene.sphboard.models')

import re

"""
Extended Group methods ........
"""

def has_monitor(self):
    return self.__get_monitor(get_current_user())

def has_direct_monitor(self):
    return self.__get_monitor(get_current_user())

def toggle_monitor(self):
    """Toggles monitor and returns the newly created monitor, or None if an
    existing monitor was deleted."""
    if self.has_direct_monitor():
        self.has_direct_monitor().delete()
        if hasattr(self, '__monitor'): delattr(self,'__monitor')
    else:
        monitor = Monitor(user = get_current_user(),
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
        level = -1
        if user.is_authenticated():
            level = 0
            if user.is_superuser:
                level = 2
            elif group and group.get_member(user) != None:
                level = 3
        return self.filter(group = group,
                           allowview__lte = level)

    def rolemember_limitation_objects(self, group):
        return self.filter( group = group )



class Category(models.Model):
    name = models.CharField(maxlength = 250)
    group = models.ForeignKey(Group, null = True, blank = True)
    parent = models.ForeignKey('self', related_name = '_childs', null = True, blank = True)
    description = models.TextField(blank = True)
    allowview = models.IntegerField( default = -1, choices = POSTS_ALLOWED_CHOICES )
    allowthreads = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    allowreplies = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    sortorder = models.IntegerField( default = 0, null = False )

    category_type = models.CharField(maxlength = 250, blank = True, db_index = True)

    objects = AccessCategoryManager()#models.Manager()
    sph_objects = AccessCategoryManager()


    changelog = ( ( '2007-04-14 00', 'alter', 'ADD sortorder INTEGER' ),
                  ( '2007-04-14 01', 'update', 'SET sortorder = 0' ),
                  ( '2007-04-14 02', 'alter', 'ALTER sortorder SET NOT NULL' ),
                  
                  ( '2007-09-03 00', 'alter', 'ADD category_type varchar(250)' ),
                  ( '2007-09-03 01', 'update', "SET category_type = ''" ),
                  ( '2007-09-03 02', 'alter', 'ALTER category_type SET NOT NULL' ),
                  )

    sph_permission_flags = { 'sphboard_editallposts':
                             'Allow editing of all posts.',

                             'sphboard_annotate':
                             'Allow annotating users posts.',

                             'sphboard_move':
                             'Allow moving of users posts.',

                             'sphboard_sticky':
                             'Allow marking threads as sticky.',

                             'sphboard_lock':
                             'Allow locking of threads.',

                             'sphboard_post_threads':
                             'Allow creating new threads.',

                             'sphboard_post_replies':
                             'Allow posting of replies to existing threads.',

                             'sphboard_view':
                             'Allows viewing of threads.',
                             }

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
        return self.threadinformation_set.select_related( depth = 1 )

    def threadCount(self):
        return self.threadinformation_set.count()

    def postCount(self):
        return self.posts.count()

    def get_latest_post(self):
        return self.posts.latest( 'postdate' )

    # For backward compatibility ...
    latestPost = get_latest_post

    def allowPostThread(self, user):
        return self.testAllowance(user, self.allowthreads) \
               or has_permission_flag(user, 'sphboard_post_threads', self)

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
        
        return user.has_perm( 'sphboard.add_post' );

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
            categoryLastVisit.lastvisit = datetime.today()
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
        if getattr(self, '_touched', False): return self._lastVisit
        self._touched = True
        self.__hasNewPosts = self._hasNewPosts(session, user)
        if not user.is_authenticated(): return None
        try:
            lastVisit = CategoryLastVisit.objects.get( category = self, user = user )

            if not lastVisit.oldlastvisit:
                if self.__hasNewPosts:
                    # Only set oldlastvisit if we have new posts.
                    lastVisit.oldlastvisit = lastVisit.lastvisit

        except CategoryLastVisit.DoesNotExist:
            lastVisit = CategoryLastVisit(user = user, category = self)
        lastVisit.lastvisit = datetime.today()
        self._lastVisit = lastVisit.oldlastvisit or lastVisit.lastvisit
        lastVisit.save()
        return self._lastVisit

    def hasNewPosts(self):
        return self._hasNewPosts(get_current_session(), get_current_user())

    def _hasNewPosts(self, session, user):
        if hasattr(self, '__hasNewPosts'): return self.__hasNewPosts
        if not user.is_authenticated(): return False
        try:
            latestPost = Post.objects.filter( category = self ).latest( 'postdate' )
        except Post.DoesNotExist:
            return False

        # Retrieve last visit ...
        try:
            lastVisit = CategoryLastVisit.objects.get( category = self, user = user )
        except CategoryLastVisit.DoesNotExist:
            return False

        # If there was no last visit, we didn't store any last visits for threads.
        # (Because there was no new threads between 'lastvisit' and 'oldlastvisit'
        #  so use 'lastvisit')
        lastvisit = lastVisit.oldlastvisit or lastVisit.lastvisit
        
        if lastvisit > latestPost.postdate:
            return False

        # Check all posts to see if they are new ....
        allNewPosts = Post.objects.filter( category = self,
                                           postdate__gt = lastvisit, )

        for post in allNewPosts:
            threadid = post.thread and post.thread.id or post.id
            try:
                lasthit = ThreadLastVisit.objects.filter( user = user,
                                                          thread__id = threadid, )[0]
            except IndexError:
                return True
            if lasthit.lastvisit < post.postdate:
                return True

        # All posts are read .. cool.. we can remove all ThreadLastVisit and adapt CategoryLastVisit
        ThreadLastVisit.objects.filter( user = user,
                                        thread__category = self, ).delete()
        lastVisit.oldlastvisit = None
        lastVisit.save()
        return False

    def toggle_monitor(self):
        """Either creates a monitor if there is none currently, or deletes an
        existing monitor."""
        
        if self.has_direct_monitor():
            self.__get_monitor(get_current_user()).delete()
            if hasattr(self, '__monitor'): delattr(self,'__monitor')
        else:
            monitor = Monitor(group = self.group,
                              user = get_current_user(),
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
        return ('sphene.sphboard.views.showCategory', (), { 'groupName': self.group.name, 'category_id': self.id })
    get_absolute_url = permalink(get_absolute_url, get_current_request)

    def get_absolute_url_rss_latest_threads(self):
        """ Returns the absolute url to the RSS feed displaying the latest threads.
        This will only work since django changeset 4901 (>0.96) """
        return reverse( 'sphboard-feeds',
                        urlconf = get_urlconf(),
                        kwargs = { 'groupName': self.group.name,
                                   'url': 'latest/%d' % self.id } )
    
    def __str__(self):
        return self.name;

    class Meta:
        ordering = ['sortorder']
    
    class Admin:
        list_display = ('name', 'group', 'parent', 'allowview', )
        list_filter = ('group', 'parent', )
        search_fields = ('name')



class ThreadLastVisit(models.Model):
    """ Entity which stores when a thread was last read. """
    user = models.ForeignKey(User)
    lastvisit = models.DateTimeField()
    thread = models.ForeignKey('Post')

    class Meta:
        unique_together = (( "user", "thread", ),)

class CategoryLastVisit(models.Model):
    """ Entity which stores when a category was last accessed. """
    user = models.ForeignKey(User)
    lastvisit = models.DateTimeField()
    oldlastvisit = models.DateTimeField(null = True,)
    category = models.ForeignKey(Category)


    changelog = ( ( '2007-06-15 00', 'alter', 'ADD oldlastvisit timestamp with time zone' ),
                  )


    class Admin:
        list_display = ('user', 'lastvisit')
        list_filter = ('user',)
        pass

POST_STATUS_DEFAULT = 0
POST_STATUS_STICKY = 1
POST_STATUS_CLOSED = 2
POST_STATUS_POLL = 4
POST_STATUS_ANNOTATED = 8

POST_STATUSES = {
    'default': 0,
    'sticky': 1,
    'closed': 2,

    'poll': 4,
    'annotated': 8,
    }

from django.contrib.auth.models import AnonymousUser

class Post(models.Model):
    status = models.IntegerField(default = 0, editable = False )
    category = models.ForeignKey(Category, related_name = 'posts', editable = False )
    subject = models.CharField(maxlength = 250)
    body = models.TextField()
    thread = models.ForeignKey('self', null = True, editable = False )
    postdate = models.DateTimeField( auto_now_add = True, editable = False )
    author = models.ForeignKey(User, editable = False, null = True, blank = True )
    markup = models.CharField(maxlength = 250,
                              null = True,
                              choices = POST_MARKUP_CHOICES, )

    changelog = ( ( '2007-04-07 00', 'alter', 'ALTER author_id DROP NOT NULL', ),
                  ( '2007-06-16 00', 'alter', 'ADD markup varchar(250) NULL', ),
                  )

    def is_sticky(self):
        return self.status & POST_STATUS_STICKY
    def is_closed(self):
        return self.status & POST_STATUS_CLOSED
    def is_poll(self):
        return self.status & POST_STATUS_POLL
    def is_annotated(self):
        return self.status & POST_STATUS_ANNOTATED

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

    def get_thread(self):
        if self.thread == None: return self;
        return self.thread;

    def get_threadinformation(self):
        return ThreadInformation.objects.type_default().get( root_post = self.get_thread() )

    def get_latest_post(self):
        return self.get_all_posts().latest( 'postdate' )

    def get_all_posts(self):
        return Post.objects.filter( Q( pk = self.id ) | Q( thread = self ) )

    def replies(self):
        return Post.objects.filter( thread = self )

    def postCount(self):
        return self.get_all_posts().count()

    def replyCount(self):
        return self.replies().count()

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
            return False
        
        return user == self.author or user.is_superuser \
               or has_permission_flag( user, 'sphboard_editallposts', self.category )
    allowEditing = allow_editing

    def _allow_adminfunctionality(self, flag, user = None):
        if user == None:
            user = get_current_user()

        if not user or not user.is_authenticated():
            return False

        return user.is_staff or has_permission_flag( user, flag, self.category )

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
        return self._allow_adminfunctionality( 'sphboard_stick', user )

    def __get_render_cachekey(self):
        return 'sphboard_rendered_body_%d' % self.id

    def body_escaped(self):
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

        if self.author_id:
            signature = get_rendered_signature( self.author_id )
            if signature:
                bodyhtml += '<div class="signature">%s</div>' % signature
        return bodyhtml

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
        if not self._hasNewPosts(session, user): return
        thread = self.thread or self
        try:
            threadLastVisit = ThreadLastVisit.objects.filter( user = user,
                                                              thread = thread, )[0]
        except IndexError:
            threadLastVisit = ThreadLastVisit( user = user,
                                               thread = thread, )

        threadLastVisit.lastvisit = datetime.today()
        threadLastVisit.save()

    def has_new_posts(self):
        if hasattr(self, '__has_new_posts'): return self.__has_new_posts
        self.__has_new_posts = self._hasNewPosts(get_current_session(), get_current_user())
        return self.__has_new_posts

    def get_latest_post(self):
        try:
            latestPost = Post.objects.filter( thread = self.id ).latest( 'postdate' )
        except Post.DoesNotExist:
            # if no post was found, the thread is the latest post ...
            latestPost = self
        return latestPost

    def _hasNewPosts(self, session, user):
        if not user.is_authenticated(): return False
        latestPost = self.get_latest_post()
        categoryLastVisit = self.category.touch(session, user)
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

    def toggle_monitor(self):
        if self.has_direct_monitor():
            self.__get_monitor(get_current_user()).delete()
            if hasattr(self, '__monitor'): delattr(self,'__monitor')
        else:
            thread = self.thread or self
            monitor = Monitor( thread = thread,
                               category = thread.category,
                               group = thread.category.group,
                               user = get_current_user(), )
            monitor.save()
            self.__monitor = monitor
            return monitor

    def save(self):
        if category_type is None:
            # Reset the default category_type -> it is a not null value.
            category_type = ''
            
        isnew = not self.id
        ret = super(Post, self).save()

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
                    
                subject = 'New Forum Post: %s' % self.subject
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

    def __str__(self):
        return self.subject

    def get_absolute_url(self):
        return ('sphene.sphboard.views.showThread', (), { 'groupName': self.category.group.name, 'thread_id': self.thread and self.thread.id or self.id })
    get_absolute_url = permalink(get_absolute_url, get_current_request)
    
    def get_absolute_editurl(self):
        return ('sphene.sphboard.views.post', (), { 'groupName': self.category.group.name, 'category_id': self.category.id, 'post_id': self.id })
    get_absolute_editurl = permalink(get_absolute_editurl, get_current_request)

    def get_absolute_annotate_url(self):
        return ('sphene.sphboard.views.annotate', (), { 'groupName': self.category.group.name, 'post_id': self.id })
    get_absolute_annotate_url = permalink(get_absolute_annotate_url, get_current_request)

    class Admin:
        pass


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
    markup = models.CharField(maxlength = 250,
                              null = True,
                              choices = POST_MARKUP_CHOICES, )

    def save(self):
        if not self.post.is_annotated():
            self.post.set_annotated(True)
            self.post.save()
        if not self.created:
            self.created = datetime.today()
        if not self.id:
            self.author = get_current_user()
        return super(PostAnnotation, self).save()

    def body_escaped(self):
        body = self.body
        markup = self.markup
        if not markup:
            markup = POST_MARKUP_CHOICES[0][0]
        return render_body( body, markup )

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


    def save(self):
        if self.thread_latest_postdate is None:
            self.thread_latest_postdate = self.latest_post.postdate
        
        super(ThreadInformation, self).save()

    def is_hot(self):
        if self.heat_calculated and (datetime.today() - self.heat_calculated).days > 7:
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
        # Find sticky ..
        self.sticky_value = self.root_post.is_sticky() and 1 or 0
        # Find the last post ...
        self.latest_post = self.root_post.get_latest_post()
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
        count = self.root_post.get_all_posts().filter( postdate__gte = datetime.today() - timedelta( days ) ).count()
        views = self.view_count

        age = -(self.root_post.postdate - datetime.today()).days

        heat_calculator = get_method_by_name( get_sph_setting( 'board_heat_calculator' ) )
        heat = heat_calculator( thread = self,
                                postcount = count,
                                viewcount = views,
                                age = age, )
        logger.debug( "Number of posts in the last %d days: %d - age: %d - views: %d - resulting heat: %d" % (days, count, age, views, heat) )
        self.heat = int(heat)
        self.heat_calculated = datetime.today()
        

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
        return int(math.ceil(self.root_post.postCount() / get_sph_setting( 'board_post_paging' )))

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

    ##
    ###################################

    def get_absolute_url(self):
        return ('sphene.sphboard.views.showThread', (), { 'groupName': self.category.group.name, 'thread_id': self.root_post.id })
    get_absolute_url = permalink(get_absolute_url, get_current_request)
    

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
    postheat = (100. / post_threshold * postcount)
    viewheat = (100. / view_threshold * (viewcount/age))

    # Subtract 100 to have non-hot topic <0
    heat = (postheat + viewheat) - 100

    return heat

def update_heat():
    """
    This method should be regularly called through a cronjob or similar -
    this can be done by simply dispatching the maintenance signal.

    see sphenecoll/sphene/community/signals.py for more details.
    """
    all_threads = ThreadInformation.objects.all()
    for thread in all_threads:
        thread.update_heat()
        thread.save()

dispatcher.connect(update_heat,
                   signal = sphene.community.signals.maintenance, )

def update_thread_information(instance):
    """
    Updates the thread information every time a post is saved.
    """
    thread = instance.get_thread()
    threadinfos = ThreadInformation.objects.filter( root_post = thread )
    
    if len(threadinfos) < 1:
        threadinfos = ( ThreadInformation( root_post = instance,
                                           category = instance.category,
                                           thread_type = THREAD_TYPE_DEFAULT, ),  )
    for threadinfo in threadinfos:
        threadinfo.update_cache()
        threadinfo.save()


dispatcher.connect(update_thread_information,
                   sender = Post,
                   signal = signals.post_save)


class Monitor(models.Model):
    """Monitors allow user to get notified by email on new posts in a
    particular thread, category or a whole board of a group."""
    
    thread = models.ForeignKey(Post, null = True, blank = True)
    category = models.ForeignKey(Category, null = True, blank = True)
    group = models.ForeignKey(Group)
    user = models.ForeignKey(User)

    class Admin:
        list_display = ('user', 'group', 'category', 'thread')
        list_filter = ('user', 'group')


class Poll(models.Model):
    post = models.ForeignKey(Post, editable = False)
    question = models.CharField( maxlength = 250 )
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

    class Admin:
        pass

class PollChoice(models.Model):
    poll = models.ForeignKey(Poll, editable = False)
    choice = models.CharField( maxlength = 250 )
    count = models.IntegerField()

    class Admin:
        pass

class PollVoters(models.Model):
    poll = models.ForeignKey(Poll, editable = False)
    choice = models.ForeignKey(PollChoice, null = True, blank = True, editable = False)
    user = models.ForeignKey(User, editable = False)



class BoardUserProfile(models.Model):
    user = models.ForeignKey( User, unique = True)
    signature = models.TextField()
    
    markup = models.CharField(maxlength = 250,
                              null = True,
                              choices = POST_MARKUP_CHOICES, )

    default_notifyme_value = models.BooleanField(null = True, )

    def render_signature(self):
        return render_body(self.signature, self.markup)



from django import newforms as forms
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display

def __get_signature_cachekey(user_id):
    return 'sphboard_signature_%s' % user_id

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

def clear_signature_cache(instance):
    cache.delete( __get_signature_cachekey( instance.user.id ) )


dispatcher.connect(clear_signature_cache,
                   sender = BoardUserProfile,
                   signal = signals.post_save)


def board_profile_edit_init_form(sender, instance, signal, *args, **kwargs):
    user = instance.user
    try:
        profile = BoardUserProfile.objects.get( user = user, )
    except:
        profile = BoardUserProfile( user = user )

    instance.fields['board_settings'] = Separator()
    instance.fields['signature'] = forms.CharField( widget = forms.Textarea( attrs = { 'rows': 3, 'cols': 40 } ),
                                                    required = False,
                                                    initial = profile.signature, )
    if len( POST_MARKUP_CHOICES ) != 1:
        instance.fields['markup'] = forms.CharField( widget = forms.Select( choices = POST_MARKUP_CHOICES, ),
                                                     required = False,
                                                     initial = profile.markup, )
    instance.fields['default_notifyme_value'] = forms.NullBooleanField( label = 'Default Notify Me - Value',
                                                                        required = False,
                                                                        initial = profile.default_notifyme_value, )

def board_profile_edit_save_form(sender, instance, signal, request):
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
    request.user.message_set.create( message = "Successfully saved board profile." )

def board_profile_display(sender, signal, request, user):
    try:
        profile = BoardUserProfile.objects.get( user = user, )
    except BoardUserProfile.DoesNotExist:
        return None

    if profile.signature:
        return '<tr><th colspan="2">Board Signature</th></tr><tr><td colspan="2">%s</td></tr>' % profile.render_signature()
    return None

dispatcher.connect(board_profile_edit_init_form, signal = profile_edit_init_form, sender = EditProfileForm)
dispatcher.connect(board_profile_edit_save_form, signal = profile_edit_save_form, sender = EditProfileForm)
dispatcher.connect(board_profile_display, signal = profile_display)
