from django import template
    
register = template.Library()

def define_page_range(page, pages):
    window = 6
    page_range = range( 1, pages+1 )

    pg = page
    out = []

    if page == -1:
        out = set(page_range[:window/2])
        out.update(set(page_range[-window/2:]))
        out = sorted(out)
        out = list(out)
        if len(out) < len(page_range):
            out.insert(window/2, '...')
    else:
        wnd_start = page_range[:pg]
        wnd_end = page_range[pg:]

        end_correction = window/2
        if len(wnd_start) <= window/2:
            end_correction = window/2 + (window/2-len(wnd_start)) + 1

        start_correction = window/2 + 1
        if len(wnd_end) <= window/2:
            start_correction = window/2 + (window/2-len(wnd_end)) + 1

        out = wnd_start[-start_correction:]
        out = out + wnd_end[:end_correction]
    return out

@register.inclusion_tag('sphene/community/_pagination.html', takes_context=True)
def sph_pagination(context, pages, page, url = '', getparam = 'page', compress=0):
    has_next = page < pages
    has_prev = page > 1
    if page == -1:
        has_next = has_prev = False


    if compress:
        page_range = define_page_range(page, pages)

        first = 1
        last = pages

        if first in page_range:
            first = None

        if last in page_range:
            last = None
    else:
        page_range = range( 1, pages+1 )
        first = None
        last = None

    to_return = {'page_range': page_range,
                 'page': page,
                 'pages': pages,
                 'has_next': has_next,
                 'has_prev': has_prev,
                 'next': page + 1,
                 'prev': page - 1,
                 'url': url,
                 'getparam': getparam,
                 'first_page':first,
                 'last_page':last
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
