from django.conf import settings
from sphene.community.models import Navigation
from sphene.community.middleware import get_current_group, get_current_sphdata

def navigation(request):
    if 'group' in request.attributes:
        group = request.attributes['group']
    else:
        group = get_current_group()
    sphdata = get_current_sphdata()

    sph_settings = getattr( settings, 'SPH_SETTINGS', None )
    if group:
        return { 'navigation_left': Navigation.objects.filter( group = group,
                                                               navigationType = 0 ),
                 'urlPrefix': request.attributes.get('urlPrefix', ''),
		 'group': group,
                 'sph': sphdata,
                 'sph_settings': sph_settings,
                 }
    return { 'sph': sphdata,
             'sph_settings': sph_settings,
             }
