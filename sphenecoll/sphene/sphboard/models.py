from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from sphene.community.models import Group

from django.utils import html
from django.conf import settings
from sphene.contrib.libs.common.text import bbcode
bbcode.EMOTICONS_ROOT = settings.MEDIA_URL + 'sphene/emoticons/'
from datetime import datetime

#from django.db.models import permalink
from sphene.community.sphutils import sphpermalink as permalink, get_sph_setting, get_urlconf, get_method_by_name
from sphene.community.templatetags.sph_extras import sph_markdown
from django.core import exceptions
from django.core.urlresolvers import reverse
from django.core.mail import send_mass_mail
from django.template.context import RequestContext
from django.template import loader, Context
from sphene.community.middleware import get_current_request, get_current_user, get_current_group, get_current_session
from sphene.sphwiki import wikilink_utils

import logging

logger = logging.getLogger('sphene.sphwiki.models')


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

# Create your models here.
class Category(models.Model):
    name = models.CharField(maxlength = 250)
    group = models.ForeignKey(Group, null = True, blank = True)
    parent = models.ForeignKey('self', related_name = '_childs', null = True, blank = True)
    description = models.TextField(blank = True)
    allowview = models.IntegerField( default = -1, choices = POSTS_ALLOWED_CHOICES )
    allowthreads = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    allowreplies = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    sortorder = models.IntegerField( default = 0, null = False )

    objects = models.Manager()
    sph_objects = AccessCategoryManager()


    changelog = ( ( '2007-04-14 00', 'alter', 'ADD sortorder INTEGER' ),
                  ( '2007-04-14 01', 'update', 'SET sortorder = 0' ),
                  ( '2007-04-14 02', 'alter', 'ALTER sortorder SET NOT NULL' ),
                  )

    def do_init(self, initializer, session, user):
        self._initializer = initializer
        self._session = session
        self._user = user
        self.touch( session, user )

    def get_children(self):
        """ Returns all children of this category in which the user has view permission. """
        return Category.sph_objects.filter_for_group( self.group ).filter( parent = self )

    def canContainPosts(self):
        return self.allowthreads != 3

    def thread_list(self):
        return self.posts.filter( thread__isnull = True )

    def threadCount(self):
        return self.posts.filter( thread__isnull = True ).count()

    def postCount(self):
        return self.posts.count()

    def latestPost(self):
        return self.posts.latest( 'postdate' )

    def allowPostThread(self, user):
        return self.testAllowance(user, self.allowthreads)

    def has_view_permission(self, user = None):
        return self.testAllowance(user or get_current_user(), self.allowview)

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
        if not lastVisit.oldlastvisit:
            return lastVisit.lastvisit < latestPost.postdate
        
        if lastVisit.oldlastvisit > latestPost.postdate:
            return False

        # Check all posts to see if they are new ....
        allNewPosts = Post.objects.filter( category = self,
                                           postdate__gt = lastVisit.oldlastvisit, )

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

ALLOWED_TAGS = {
    'p': ( 'align' ),
    'em': (),
    'strike': (),
    'strong': (),
    'img': ( 'src', 'width', 'height', 'border', 'alt', 'title' ),
    'u': ( ),
    }

#USED_STYLE = 'html'
USED_STYLE = 'bbcode'

def htmlentities_replace(test):
    print "entity allowed: %s" % test.group(1)
    return test.group()

def htmltag_replace(test):
    if ALLOWED_TAGS.has_key( test.group(2) ):
        print "tag is allowed.... %s - %s" % (test.group(), test.group(3))
        if test.group(3) == None: return test.group()
        attrs = test.group(3).split(' ')
        allowedParams = ALLOWED_TAGS[test.group(2)]
        i = 1
        allowed = True
        for attr in attrs:
            if attr == '': continue
            val = attr.split('=')
            if not val[0] in allowedParams:
                allowed = False
                print "Not allowed: %s" % val[0]
                break
        if allowed: return test.group()
    print "tag is not allowed ? %s" % test.group(2)
    return test.group().replace('<','&lt;').replace('>','&gt;')

def bbcode_replace(test):
    print "bbcode ... %s %s %s" % (test.group(1), test.group(2), test.group(3))
    return test.group()

def bbcode_render(body):
    return wikilink_utils.render_wikilinks(bbcode.bb2xhtml(body))

def html_render(body):
    """DISABLED.  Render the body as html"""
    if False:
        regex = re.compile("&(?!nbsp;)");
        body = regex.sub( "&amp;", body )
        regex = re.compile("<(/?)([a-zA-Z]+?)( .*?)?/?>")
        return regex.sub( htmltag_replace, body )
    return ""

POST_STATUS_DEFAULT = 0
POST_STATUS_STICKY = 1
POST_STATUS_CLOSED = 2
POST_STATUS_POLL = 4

POST_STATUSES = {
    'default': 0,
    'sticky': 1,
    'closed': 2,

    'poll': 4,
    }

AVAILABLE_MARKUP = {
    'bbcode': 'BBCode',
    'markdown': 'Markdown',
    }
# Markup choices used for the 'choices' option for model fields.
POST_MARKUP_CHOICES = ( )

enabled_markup = get_sph_setting( 'board_markup_enabled', ( 'bbcode', ) )
custom_markup = get_sph_setting( 'board_custom_markup', {} )

render_functions = {
    'bbcode' : bbcode_render,
    'markdown' : sph_markdown,
    'html' : html_render,
}

for en in enabled_markup:
    try:
        POST_MARKUP_CHOICES += ( ( en, AVAILABLE_MARKUP[en] ), )
    except KeyError:
        try:
            POST_MARKUP_CHOICES += ( ( en, custom_markup[en] ), )
        except KeyError:
            raise exceptions.ImproperlyConfigured(
                "Custom renderer '%s' needs a matching label entry in your "
                 % en + "sphene settings 'board_custom_markup'")
        render_functions[en] = get_method_by_name(en)

from django.contrib.auth.models import AnonymousUser

def render_body(body, markup = None):
    """ Renders the given body string using the given markup.
    """
    if markup:
        try:
            return render_functions[markup](body)
        except KeyError:
            raise exceptions.ImproperlyConfigured(
                "Can't render markup '%s'" % markup)
    else:
        return body

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

    def do_init(self, initializer, session, user):
        self._initializer = initializer
        self.hasNewPosts = self._hasNewPosts(session, user)

    def is_sticky(self):
        return self.status & POST_STATUS_STICKY
    def is_closed(self):
        return self.status & POST_STATUS_CLOSED
    def is_poll(self):
        return self.status & POST_STATUS_POLL

    def set_sticky(self, sticky):
        if sticky: self.status = self.status | POST_STATUS_STICKY
        else: self.status = self.status ^ POST_STATUS_STICKY

    def set_closed(self, closed):
        if closed: self.status = self.status | POST_STATUS_CLOSED
        else: self.status = self.status ^ POST_STATUS_CLOSED

    def set_poll(self, poll):
        if poll: self.status = self.status | POST_STATUS_POLL
        else: self.status = self.status ^ POST_STATUS_POLL

    def get_thread(self):
        if self.thread == None: return self;
        return self.thread;

    def latestPost(self):
        return self.allPosts().latest( 'postdate' )

    def allPosts(self):
        return Post.objects.filter( Q( pk = self.id ) | Q( thread = self ) )

    def replies(self):
        return Post.objects.filter( thread = self )

    def postCount(self):
        return self.allPosts().count()

    def replyCount(self):
        return self.replies().count()

    def allowPosting(self, user):
        return self.category.testAllowance( user, self.category.allowreplies )

    def allowEditing(self, user = None):
        if user == None: user = get_current_user()
        return user == self.author or user.is_superuser


    def body_escaped(self):
        """ returns the rendered body. """
        body = self.body
        markup = self.markup
        if not markup:
            markup = POST_MARKUP_CHOICES[0][0]

        bodyhtml = render_body( body, markup )
        if self.author:
            signature = get_rendered_signature( self.author )
            if signature:
                bodyhtml += '<div class="signature">%s</div>' % signature
        return bodyhtml

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
        isnew = not self.id
        ret = super(Post, self).save()

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

    class Admin:
        pass




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

    def do_init(self, initializer, session, user):
        self._initializer = initializer
        self._user = user
        
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



from django.dispatch import dispatcher
from django import newforms as forms
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display

def get_rendered_signature(user):
    """ Returns the rendered signature for the given user. """
    # TODO add caching !
    try:
        profile = BoardUserProfile.objects.get( user = user, )
    except BoardUserProfile.DoesNotExist:
        return None
    return profile.render_signature()


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
