from django.conf import settings
from sphene.community.models import Navigation
from sphene.community.permissionutils import has_permission_flag
from sphene.community.sphutils import SphSettings
from sphene.community.middleware import get_current_group, get_current_sphdata, get_current_user


class PermissionFlagLookup(object):
    def __getitem__(self, flag_name):
        return has_permission_flag(get_current_user(), flag_name)


def navigation(request):
    if hasattr(request, 'attributes') and 'group' in request.attributes:
        group = request.attributes['group']
    else:
        group = get_current_group()
    sphdata = get_current_sphdata()

    sph_settings = getattr( settings, 'SPH_SETTINGS', None )
    sphdata['installed_apps'] = settings.INSTALLED_APPS
    sphdata['current_url'] = request.path
    querystring = request.META.get('QUERY_STRING', None)
    if querystring:
        sphdata['current_url'] += '?'+querystring
    # urlPrefix is deprecated, don't use it.
    urlPrefix = ''
    if hasattr(request, 'attributes'):
        urlPrefix = request.attributes.get('urlPrefix', '')
    if group:
        return { 'navigation_left': Navigation.objects.filter( group = group,
                                                               navigationType = 0 ),
                 'urlPrefix': urlPrefix,
                 'group': group,
                 'sph': sphdata,
                 'sph_settings': SphSettings(),
                 'sph_perms': PermissionFlagLookup(),
                 }
    return { 'sph': sphdata,
             'sph_settings': SphSettings(),
             'sph_perms': PermissionFlagLookup(),
             }
