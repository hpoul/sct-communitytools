"""

### Testing simple posts ...


# Create us a test user ..
>>> from django.contrib.auth.models import User
>>> testuser = User.objects.create_user( 'sometestuser', 'testuser@sphene.net', 'testpassword' )
>>> testuser.save()

>>> testuser2 = User.objects.create_user( 'sometestuser2', 'testuser2@sphene.net', 'testpassword2' )
>>> testuser2.save()

>>> from django import http
>>> from sphene.community.testutils import setup_threadlocals
>>> from sphene.community.middleware import get_current_user

>>> req = setup_threadlocals(testuser, set_group=False)
>>> get_current_user().username
'sometestuser'

>>> from sphene.sphboard.models import Post, Category
>>> c = Category.objects.get( name = 'Example Category' )

>>> c.has_new_posts()
False

# Touch the category, ignore output
>>> c.touch(req.session, req.user) == None
False

>>> p = Post( category = c, subject = 'Test Subject', 
...           body = "Some body", markup = 'bbcode', author = testuser )
>>> p.save()
>>> p.author.username
u'sometestuser'

# Install monitor
>>> p.toggle_monitor() == None
False

# Check flag options
>>> p.is_sticky()
0
>>> p.is_poll()
0
>>> p.is_closed()
0

######
# Verify display of new posts for category
>>> c.has_new_posts()
True

# Touch the category, ignore output
>>> c = Category.objects.get( pk = c.id )
>>> c.touch(req.session, req.user) == None
False

>>> p.has_new_posts()
True

>>> p.touch(req.session, req.user) == None
True


>>> c = Category.objects.get( pk = c.id )
>>> c.has_new_posts()
False

#
######


>>> p.get_threadinformation().post_count
1
>>> p2 = Post( category = c, subject = 'Re: Test Subject', body = "some reply", markup = 'bbcode', thread = p, author = testuser2 )
>>> p2.save()

#######
# Again check new post display
>>> c.has_new_posts()
True

>>> p.touch(req.session, req.user) == None
True

>>> p.has_new_posts()
False

>>> c = Category.objects.get( pk = c.id )
>>> c.has_new_posts()
False

# Check catchup

>>> p3 = Post( category = c, subject = 'Re: Test Subject', body = "some reply", markup = 'bbcode', thread = p, author = testuser2 )
>>> p3.save()

>>> c = Category.objects.get( pk = c.id )
>>> c.has_new_posts()
True

>>> c.catchup(req.session, req.user)
>>> c = Category.objects.get( pk = c.id )
>>> c.has_new_posts()
False

>>> p = Post.objects.get( pk = p.id )
>>> p.has_new_posts()
False


#
#########

# Validate outgoing email ..
>>> from django.core import mail
>>> mail.outbox[0].subject
'New Forum Post: Re: Test Subject'
>>> len(mail.outbox)
2

# Validate thread information ..
>>> p = Post.objects.get( pk = p.id )
>>> p.get_threadinformation().post_count
3
>>> p.get_threadinformation().latest_post == p3
True
>>> p.get_threadinformation().view_count
0
>>> p.viewed(req.session, req.user)
>>> p.get_threadinformation().view_count
1

# Check that the category returns the correct information ..
>>> c.postCount()
3
>>> c.threadCount()
1



#####################################
#
# testing flag permission system ...
#

>>> from sphene.community import testutils
>>> from sphene.community.models import Role, RoleMember, PermissionFlag, RoleMemberLimitation
>>> from django.contrib.contenttypes.models import ContentType
>>> group = testutils.get_testgroup()
>>> req = testutils.setup_threadlocals(testuser, group)

# Verify that we don't have permission ...
>>> c.allowview = 3
>>> c.allowreplies = 3
>>> c.allowthreads = 3
>>> c.save()

>>> c.has_view_permission()
False

# First create a moderator role ...
>>> moderators = Role( name = 'Moderators', group = group )
>>> moderators.save()
>>> moderators.permission_flags.add( PermissionFlag.objects.get( name = 'sphboard_view' ) )
>>> role_member = RoleMember( role = moderators, user = testuser, has_limitations = True )
>>> role_member.save()
>>> RoleMemberLimitation( role_member = role_member, content_object = c ).save()

# Check for a second category that the user as still no right to view it.
>>> c2 = Category( name = "Second example" )
>>> c2.allowview = 3
>>> c2.save()

>>> c2.has_view_permission()
False

# Check if we have view permission in the original category ..
>>> c.has_view_permission()
True

"""

from django.test import TestCase
from sphene.community import testutils
from sphene.community.models import Role, PermissionFlag, RoleMember, RoleMemberLimitation
from sphene.sphboard.models import Category, Post

class PermissionRoleTester(TestCase):
    
    def setUp(self):
        self.testuser = testutils.get_testuser()
        self.testgroup = testutils.get_testgroup()
        testutils.setup_threadlocals(self.testuser, self.testgroup)

        # Setup test role ..
        self.testrole = testutils.get_testrole()

        # Test category
        # Since we are testing permissions .. revoke all permissions
        self.c = Category(name = 'Simple Test Category',
                          allowview = 3,
                          allowreplies = 3,
                          allowthreads = 3,)
        self.c.save()

    def __assign_flag(self, flag, role = None ):
        if not role:
            role = self.testrole

        role.permission_flags.add( PermissionFlag.objects.get( name = flag ) )

    def __add_user_to_role(self, obj = None, user = None, role = None):
        if user is None:
            user = self.testuser
        if role is None:
            role = self.testrole

        role_member = RoleMember( role = role,
                                  user = user,
                                  has_limitations = obj is not None )
        role_member.save()

        if obj is not None:
            RoleMemberLimitation( role_member = role_member,
                                  content_object = obj, ).save()

    def __create_testpost(self):
        # Create post ...
        p = Post( category = self.c, subject = 'Just a test post', body = 'hehe', author = self.testuser )
        p.save()
        return p

    def test_view_permission(self):
        self.failIf(self.c.has_view_permission(), 'Verify that we do not have view permission.')
        self.__assign_flag( 'sphboard_view' )
        self.__add_user_to_role( self.c )
        self.failUnless(self.c.has_view_permission(), "Verify we have view permission.")

    def test_post_threads_permission(self):
        self.__assign_flag( 'sphboard_post_threads' )
        self.failIf(self.c.allowPostThread(self.testuser), 'Verify that we do not have post thread permission.')
        self.__add_user_to_role( self.c )
        self.failUnless(self.c.allowPostThread(self.testuser), 'Verify that we have post thread permission.')

    def test_post_replies_permission(self):
        p = self.__create_testpost()
        self.__add_user_to_role( self.c )
        self.failIf(p.allow_posting(self.testuser), 'Verify that we do not have repy permission.')
        self.__assign_flag( 'sphboard_post_replies' )
        self.failUnless(p.allow_posting(self.testuser), 'Verify that wehave reply permission.')

    def test_allow_editing(self):
        p = self.__create_testpost()
        # I know we can edit it, since we are the original author ..
        self.failUnless(p.allow_editing())
        p.author = testutils.get_superuser()
        p.save()
        # Now we must not have edit permission
        self.failIf(p.allow_editing())
        self.__add_user_to_role( self.c )
        self.__assign_flag( 'sphboard_editallposts' )
        self.failUnless(p.allow_editing())

