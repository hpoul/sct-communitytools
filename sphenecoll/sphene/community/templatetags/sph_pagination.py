from collections import deque
from itertools import count
from django import template
    
register = template.Library()


def define_page_range(current_page, total_pages, window=6):
    """ Returns range of pages that contains current page and few pages before and after it.

        @current_page - starts from 1
        @tota_pages - total number of pages
        @window - maximum number of pages shown with current page - should be even

        Examples (cucumber style):
             Given window = 6
             When current_page is 8
             and total_pages = 20
             Then I should see: 5 6 7 [8] 9 10 11

             Given window = 6
             When current_page is 8
             and total_pages = 9
             Then I should see: 3 4 5 6 7 [8] 9

             Given window = 6
             When current_page is 1
             and total_pages = 9
             Then I should see: [1] 2 3 4 5 6 7
    """
    # maximum length of page range is window + 1
    maxlen = window + 1
    page_range = deque(maxlen=maxlen)

    # minimum possible index is either: (current_page - window) or 1
    window_start = (current_page - window) if (current_page - window) > 0 else 1

    # maximum possible index is current_page + window or total_pages
    window_end = total_pages if (current_page + window) > total_pages else (current_page + window)

    # if we have enough pages then we should end at preffered end
    preffered_end = current_page + int(window / 2.0)

    for i in count(window_start):
        if i > window_end:
            # if we're on first page then our window will be [1] 2 3 4 5 6 7
            break
        elif i > preffered_end and len(page_range) == maxlen:
            # if we have enough pages already then stop at preffered_end
            break
        page_range.append(i)
    return list(page_range)


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
