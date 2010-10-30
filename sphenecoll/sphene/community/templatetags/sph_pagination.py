from django import template
    
register = template.Library()



@register.inclusion_tag('sphene/community/_pagination.html', takes_context=True)
def sph_pagination(context, pages, page, url = '', getparam = 'page'):
    has_next = page < pages
    has_prev = page > 1
    if page == -1:
        has_next = has_prev = False

    to_return = {'page_range': range( 1, pages+1 ),
                 'page': page,
                 'pages': pages,
                 'has_next': has_next,
                 'has_prev': has_prev,
                 'next': page + 1,
                 'prev': page - 1,
                 'url': url,
                 'getparam': getparam,
                 }

    if 'request' in context:
        getvars = context['request'].GET.copy()
        if 'page' in getvars:
            del getvars['page']
        if len(getvars.keys()) > 0:
            to_return['getvars'] = "&%s" % getvars.urlencode()
        else:
            to_return['getvars'] = ''
        
    return to_return
