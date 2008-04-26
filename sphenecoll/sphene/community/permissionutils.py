
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from sphene.community.middleware import get_current_group
from sphene.community.models import Role, RoleMember, PermissionFlag, RoleGroupMember


def has_permission_flag(user, flag, contentobject = None, group = None):
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

    if group is None:
        group = get_current_group()
    
    # TODO cache rolegroup_ids for user ?
    rolegroups = RoleGroupMember.objects.filter(rolegroup__group = group, user = user)
    rolegroup_ids = [rolegroup.rolegroup_id for rolegroup in rolegroups]

    # Check if the user has a global flag ...
    userselect = (Q(user = user) & Q(rolegroup__isnull = True)) \
        | (Q(rolegroup__in = rolegroup_ids) & Q(user__isnull = True))
    matches = RoleMember.objects.filter( 
        userselect,
        role__permission_flags__name__exact = flag, has_limitations = False ).count()

    if matches > 0:
        return True

    # if it wasn't found ...
    # ... lookup flag for the given model:
    if contentobject is not None:
        content_type = ContentType.objects.get_for_model(contentobject)
        rolemembers = RoleMember.objects.filter( userselect,
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
