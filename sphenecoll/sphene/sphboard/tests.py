"""

### Testing simple posts ...


# Create us a test user ..
>>> from django.contrib.auth.models import User
>>> testuser = User.objects.create_user( 'sometestuser', 'testuser@sphene.net', 'testpassword' )
>>> testuser.save()

>>> testuser2 = User.objects.create_user( 'sometestuser2', 'testuser2@sphene.net', 'testpassword2' )
>>> testuser2.save()

>>> from django import http
>>> from django.contrib.sessions.middleware import SessionWrapper
>>> from sphene.community.middleware import ThreadLocals, get_current_user

# Initialize thread locals ...
>>> req = http.HttpRequest()
>>> req.session = SessionWrapper(None)

# Store the test user as current user ...
>>> req.user = testuser
>>> ThreadLocals().process_request( req )

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



"""
