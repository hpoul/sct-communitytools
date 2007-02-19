from sphene.community.models import Navigation
from sphene.community.middleware import get_current_group

def navigation(request):
    if 'group' in request.attributes:
        group = request.attributes['group']
    else:
        group = get_current_group()
    if group:
        return { 'navigation_left': Navigation.objects.filter( group = group,
                                                               navigationType = 0 ),
                 'urlPrefix': request.attributes.get('urlPrefix', ''),
		 'group': group, }
    return { }
