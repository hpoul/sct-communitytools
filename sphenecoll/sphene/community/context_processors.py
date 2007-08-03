from django.conf import settings
from sphene.community.models import Navigation
from sphene.community.middleware import get_current_group, get_current_sphdata

def navigation(request):
    if hasattr(request, 'attributes') and 'group' in request.attributes:
        group = request.attributes['group']
    else:
        group = get_current_group()
    sphdata = get_current_sphdata()

    sph_settings = getattr( settings, 'SPH_SETTINGS', None )
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
                 'sph_settings': sph_settings,
                 }
    return { 'sph': sphdata,
             'sph_settings': sph_settings,
             }
