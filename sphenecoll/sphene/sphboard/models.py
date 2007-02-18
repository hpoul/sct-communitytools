from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User

from sphene.community.models import Group

from django.utils import html
from text import bbcode
from datetime import datetime

import re

POSTS_ALLOWED_CHOICES = (
    (-1, 'All Users'),
    (0, 'Loggedin Users'),
    (1, 'Members of the Group'),
    (2, 'Administrators'),
    (3, 'Nobody'),
    )

# Create your models here.
class Category(models.Model):
    name = models.CharField(maxlength = 250)
    group = models.ForeignKey(Group, null = True, blank = True)
    parent = models.ForeignKey('self', related_name = '_childs', null = True, blank = True)
    description = models.TextField(blank = True)
    allowthreads = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )
    allowreplies = models.IntegerField( default = 0, choices = POSTS_ALLOWED_CHOICES )

    def do_init(self, initializer, session, user):
        self._initializer = initializer
        self._session = session
        self._user = user
        self.touch( session, user )

    def get_childs(self):
        return self._childs.all().add_initializer(getattr(self, '_initializer', None))

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

    def testAllowance(self, user, level):
        if level == -1:
            return True;
        if user == None or not user.is_authenticated():
            return False;
        if level == 0:
            return True;
        return False;

    """
      Touches the category object by updating 'lastVisit'
      Returns the datetime object of when it was last visited.
    """
    def touch(self, session, user):
        # Check if we were already "touched" ;)
        if getattr(self, '_touched', False): return self._lastVisit
        self._touched = True
        self.hasNewPosts = self._hasNewPosts(session, user)
        if not user.is_authenticated(): return None
        try:
            lastVisit = CategoryLastVisit.objects.get( category = self, user = user )
            sKey = self._getSessionKey()
            val = session.get( sKey )
            if not val or not val.has_key( 'originalLastVisit' ):
                val = { 'originalLastVisit': lastVisit.lastvisit,
                        'originalLastVisitSet': datetime.today(), }
                session[sKey] = val
            self._lastVisit = val['originalLastVisit']
        except CategoryLastVisit.DoesNotExist:
            lastVisit = CategoryLastVisit(user = user, category = self)
            self._lastVisit = datetime.today()
        lastVisit.lastvisit = datetime.today()
        lastVisit.save()
        return self._lastVisit

    def _hasNewPosts(self, session, user):
        if not user.is_authenticated(): return False
        try:
            latestPost = Post.objects.filter( category = self ).latest( 'postdate' )
        except Post.DoesNotExist:
            return False
        
        sKey = self._getSessionKey()
        val = session.get( sKey )
        if not val or not val.has_key('originalLastVisit'):
            # if no original lastvisit is stored, load lastvisit from DB.
            try:
                lastVisit = CategoryLastVisit.objects.get( category = self, user = user )
            except CategoryLastVisit.DoesNotExist:
                return False
            return lastVisit.lastvisit < latestPost.postdate

        if val['originalLastVisit'] > latestPost.postdate:
            return False

        if not val.has_key('thread_lasthits'):
            return True

        lasthits = val['thread_lasthits']

        # Check all posts to see if they are new ....
        allNewPosts = Post.objects.filter( category = self,
                                           postdate__gt = val['originalLastVisit'], )

        for post in allNewPosts:
            threadid = post.thread and post.thread.id or post.id
            if not lasthits.has_key( threadid ) or lasthits[threadid] < post.postdate:
                return True

        # All posts are read .. cool.. we can remove 'thread_lasthits' and adept 'originalLastVisit'
        del val['thread_lasthits']
        del val['originalLastVisit']
        session[sKey] = val # Store the value back into the session so it gets stored.
        return False

    def _getSessionKey(self):
        return 'sphene_sphboard_category_%d' % self.id;

    def __str__(self):
        return self.name;
    
    class Admin:
        search_fields = ('name')

class CategoryLastVisit(models.Model):
    user = models.ForeignKey(User)
    lastvisit = models.DateTimeField()
    category = models.ForeignKey(Category)

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


class Post(models.Model):
    status = models.IntegerField(default = 0, editable = False )
    category = models.ForeignKey(Category, related_name = 'posts', editable = False )
    subject = models.CharField(maxlength = 250)
    body = models.TextField()
    thread = models.ForeignKey('self', null = True, editable = False )
    postdate = models.DateTimeField( auto_now_add = True, editable = False )
    author = models.ForeignKey(User, editable = False )

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

    def postCount(self):
        return self.allPosts().count()

    def allowPosting(self, user):
        return self.category.testAllowance( user, self.category.allowreplies )


    def body_escaped(self):
        body = self.body
        if USED_STYLE == 'html':
            regex = re.compile("&(?!nbsp;)");
            body = regex.sub( "&amp;", body )
            regex = re.compile("<(/?)([a-zA-Z]+?)( .*?)?/?>")
            return regex.sub( htmltag_replace, body )
        else:
            """
            body = html.escape( body )
            body = html.linebreaks( body )
            regex = re.compile("\[(.*?)\](?:([^\[]+)\[/(.*?)\])?")
            bbcode = regex.sub( bbcode_replace, body )
            """
            return bbcode.bb2xhtml(body)

    def touch(self, session, user):
        return self._touch( session, user )

    def _touch(self, session, user):
        if not user.is_authenticated(): return None
        if not self._hasNewPosts(session, user): return
        sKey = self.category._getSessionKey()
        val = session.get( sKey )
        if not val: val = { }
        if not val.has_key( 'thread_lasthits' ): val['thread_lasthits'] = { }
        val['thread_lasthits'][self.id] = datetime.today()
        session[sKey] = val

    def _hasNewPosts(self, session, user):
        if not user.is_authenticated(): return False
        try:
            latestPost = Post.objects.filter( thread = self.id ).latest( 'postdate' )
        except Post.DoesNotExist:
            # if no post was found, the thread is the latest post ...
            latestPost = self
        categoryLastVisit = self.category.touch(session, user)
        if categoryLastVisit > latestPost.postdate:
            return False
        sKey = self.category._getSessionKey()
        val = session.get( sKey )
        if not val or not val.has_key( 'thread_lasthits' ) or not val['thread_lasthits'].has_key(self.id):
            return True
        return val['thread_lasthits'][self.id] < latestPost.postdate

    def poll(self):
        try:
            return self.poll_set.all().add_initializer( getattr(self, '_initializer', None) ).get()
        except Poll.DoesNotExist:
            return None

    def __str__(self):
        return self.subject

    class Admin:
        pass



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
        if not user: user = self._user
        if not user.is_authenticated(): return False
        return self.pollvoters_set.filter( user = user ).count() > 0
        """try:
            return True
        except PollVoters.DoesNotExist:
            return False
        """

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

