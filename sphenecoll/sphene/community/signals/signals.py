import django.dispatch
from django.conf import settings
from django.core.cache import cache

from sphene.community.sph_cacheutils import invalidate_cache_group_id

# Called when the edit_profile view initializes the form ...
# gives listeners a chance to add custom fields to the form.
profile_edit_init_form = django.dispatch.Signal()

# Called when the edit_profile view has validated the form data and has
# saved the profile data. - Gives listeners a chance to save their form
# data previously added in profile_edit_init_form
profile_edit_save_form = django.dispatch.Signal()

# called when the profile view displays the profile of a given user.
# Listeners should return HTML code which will be added into the
# 2 column html table of the profile.
# Arguments:
#  - request (Containing the http request)
#  - user (The User from whom to display the profile.)
profile_display = django.dispatch.Signal()


# A signal which can be used to do periodic work,
# e.g. the board could recalculate the heat of threads.
# Should be called once a day.
maintenance = django.dispatch.Signal()



# This method should be regularly called (once a day) through a cron job like:
#
# echo -e "from sphene.community.signals import trigger_maintenance\ntrigger_maintenance()" | ./manage.py shell --plain
def trigger_maintenance():
    maintenance.send(None)

def clear_user_displayname(sender, instance, created, *args, **kwargs):
    from django.contrib.auth.models import User
    user = None
    if isinstance(instance, User):
        user = instance
    else:
        user = instance.user
    key = '%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, user.pk)
    cache.delete(key)

def clear_permissions_cache_rgm(sender, instance, *args, **kwargs):
    """ RoleGroupMember
    """
    invalidate_cache_group_id('has_permission_flag_%s' % (instance.user_id))

def clear_permissions_cache_rml(sender, instance, *args, **kwargs):
    """ RoleMemberLimitation
    """
    invalidate_cache_group_id('has_permission_flag_%s' % (instance.role_member.user_id))

def clear_permissions_cache_rm(sender, instance, *args, **kwargs):
    """ RoleMember
    """
    invalidate_cache_group_id('has_permission_flag_%s' % (instance.user_id))

def clear_permission_flag_cache(sender, instance, *args, **kwargs):
    """ m2mchanged
        If permissions for role had been changed then invalidate permission cache for all users in this role
    """
    from sphene.community.models import RoleMember
    user_ids = RoleMember.objects.filter(role=instance).values_list('user', flat=True)
    for user_id in user_ids:
        invalidate_cache_group_id('has_permission_flag_%s' % (user_id))

#     clear_permissions_cache_rgm, sender=RoleGroupMember)
#post_save.connect(clear_permissions_cache_rml, sender=RoleMemberLimitation)
#post_save.connect(clear_permissions_cache_rm, sender=RoleMember)
