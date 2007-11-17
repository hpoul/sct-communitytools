"""

### A few simple tests for the flag system ...



# First we create some initial data ... (user accounts)

>>> from django.contrib.auth.models import User
>>> from sphene.community import testutils
>>> from sphene.community.models import Role, RoleMember, PermissionFlag
>>> from sphene.community.permissionutils import has_permission_flag

>>> testuser = User.objects.create_user( 'communitytestuser', 'communitytestuser@sphene.net', 'testpassword' )
>>> testuser.save()

>>> testgroup = testutils.get_testgroup()

>>> has_permission_flag( testuser, 'community_manage_roles' )
False

>>> req = testutils.setup_threadlocals( testuser, testutils.get_testgroup() )

>>> has_permission_flag( testuser, 'community_manage_roles' )
False


# Check null/anonymous user (should be handled the same)
>>> has_permission_flag( None, 'community_manage_roles' )
False

# Admin user should have the right for everything
>>> superuser = testutils.get_superuser()
>>> has_permission_flag( superuser, 'doesnotexist' )
True

# Assign flag to user ...

>>> testrole = testutils.get_testrole()

>>> testrole.permission_flags.add( PermissionFlag.objects.get( name = 'community_manage_roles' ) )
>>> testrole.save()

>>> RoleMember( role = testrole, user = testuser, has_limitations = False ).save()


>>> has_permission_flag( testuser, 'community_manage_roles' )
True

# Non-existing flag ?
>>> has_permission_flag( testuser, 'doesnotexist' )
False

# admin flag ..
>>> has_permission_flag( testuser, 'group_administrator' )
False


# Remove flag from group
>>> testrole.permission_flags.clear()
>>> testrole.save()

>>> has_permission_flag( testuser, 'community_manage_roles' )
False

# Admin role
>>> testrole.permission_flags.add( PermissionFlag.objects.get( name = 'group_administrator' ) )

>>> has_permission_flag( testuser, 'community_manage_roles' )
True

"""
