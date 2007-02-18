from sphene.community.models import Navigation

def navigation(request):
    if not 'group' in request.attributes: return { }
    group = request.attributes['group']
    if group:
        return { 'navigation_left': Navigation.objects.filter( group = group,
                                                               navigationType = 0 ),
                 'urlPrefix': request.attributes['urlPrefix'] }
    return { }
