from django.conf import settings
from django.core.cache import cache

from django.db.models import Q
from django.contrib.contenttypes.models import ContentType

from sphene.community.middleware import get_current_group
from sphene.community.models import Role, RoleMember, PermissionFlag, RoleGroupMember
from sphene.community.sph_cacheutils import get_cache_group_id


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

    # group cache entries by user
    cache_group_id = get_cache_group_id('has_permission_flag_%s' % (user.pk))
    key = '%s_%s_has_perm_flag_%s_%s_%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, cache_group_id, user.pk, flag,
                                            contentobject and contentobject.pk or '0', group.pk)

    res = cache.get(key, False)
    if res:
        return res

    # TODO cache rolegroup_ids for user ?
    rolegroup_ids = RoleGroupMember.objects.filter(rolegroup__group = group, user = user).values_list('id',flat=True)

    # Check if the user has a global flag ...
    userselect = (Q(user = user) & Q(rolegroup__isnull = True)) \
        | (Q(rolegroup__in = rolegroup_ids) & Q(user__isnull = True))
    matches = RoleMember.objects.filter(
        userselect,
        role__permission_flags__name__exact = flag, has_limitations = False ).count()

    if matches > 0:
        res = True
    else:
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
                res = True

        # ... lookup the group_administrator flag:
        if not res and flag != 'group_administrator':
            res = has_permission_flag(user, 'group_administrator')
    cache.set(key, res, 86400)
    return res
