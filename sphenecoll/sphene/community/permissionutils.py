from sphene.community.models import Role, RoleMember, PermissionFlag
from django.contrib.contenttypes.models import ContentType


def has_permission_flag(user, flag, contentobject = None):
    """
    Checks if the given user has the given flag for the given model instance
    (object).
    If object is not given, it checks if the user has the flag globally
    assigned.
    """
    # Anonymous users won't have flags ...
    if user is None or not user.is_authenticated():
        return False

    # Super users have all flags anyway ..
    if user.is_superuser:
        return True
    
    # Check if the user has a global flag ...
    matches = RoleMember.objects.filter( user = user, role__permission_flags__name__exact = flag, has_limitations = False ).count()
    if matches > 0:
        return True

    # if it wasn't found ...
    # ... lookup flag for the given model:
    if contentobject is not None:
        content_type = ContentType.objects.get_for_model(contentobject)
        rolemembers = RoleMember.objects.filter( user = user,
                                                 role__permission_flags__name__exact = flag,
                                                 has_limitations = True,

                                                 rolememberlimitation__object_type = content_type,
                                                 rolememberlimitation__object_id = contentobject.id,
                                                 ).count()
        if rolemembers > 0:
            return True
            
    # ... lookup the group_administrator flag:
    if flag != 'group_administrator':
        return has_permission_flag(user, 'group_administrator')

    return False
