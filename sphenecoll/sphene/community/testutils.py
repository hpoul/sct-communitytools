

# Very simple test utils .. which are ment to set up a test
# environment
# Useful for e.g. thread locals.

from django import http
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionWrapper
from sphene.community.models import Group, Role
from sphene.community.middleware import ThreadLocals, get_current_user, set_current_group


def get_testgroup():
    try:
        return Group.objects.get( name = 'testgroup' )
    except Group.DoesNotExist:
        g = Group( name = 'testgroup',
                   longname = "Some Test Group",
                   baseurl = 'testgroup.sphene.net' )
        g.save()
        
        return g

def get_testuser():
    try:
        return User.objects.get( username = 'generaltestuser' )
    except User.DoesNotExist:
        u = User.objects.create_user( 'generaltestuser', 'generaltestuser@sphene.net', 'testpassword' )
        u.save()
        return u

def get_superuser():
    superuser = User.objects.create_user( 'supertestuser', 'supertestuser@sphene.net', 'testpassword' )
    superuser.is_superuser = True
    superuser.save()
    return superuser

def get_testrole():
    try:
        return Role.objects.get( name = 'testrole' )
    except Role.DoesNotExist:
        r = Role( name = 'testrole',
                  group = get_testgroup() )
        r.save()
        return r

def setup_threadlocals(testuser, group):
    # Initialize thread locals ...
    req = http.HttpRequest()
    req.session = SessionWrapper(None)

    # Store the test user as current user ...
    req.user = testuser
    ThreadLocals().process_request( req )

    set_current_group( group )
