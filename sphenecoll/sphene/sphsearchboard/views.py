
from django.utils.safestring import mark_safe
from django.utils.http import urlquote_plus

from sphene.community.sphutils import sph_render_to_response
from sphene.sphboard.models import Category
from sphene.sphsearchboard.models import search_posts

pagingsize = 10

def view_search_posts(request, group):
    query = request.GET.get('query', '')
    results = None
    terms = query.split(' ')
    start = 0
    end = 0
    prev = False
    next = False
    count = 0
    category = None
    category_id = request.GET.get('category_id', '')
    if category_id:
        category = Category.objects.get(pk = category_id)

    if query:
        results = search_posts(query=query, category=category)
        start = int(request.GET.get('start', 0))
        end = start + pagingsize
        count = results.count()
        results = results[start:end]

        start += 1
        if start > 1:
            prev = mark_safe(u'?query=%s&amp;start=%d&amp;category_id=%s' % (urlquote_plus(query), max(0,start-pagingsize-1), category_id))
        if end < count:
            next = mark_safe(u'?query=%s&amp;start=%d&amp;category_id=%s' % (urlquote_plus(query), end, category_id))
        if end > count:
            end = count

    return sph_render_to_response('sphene/sphsearchboard/search.html',
                                  { 'query': query,
                                    'results': results,
                                    'terms': terms,
                                    'start': start,
                                    'end': end,
                                    'prev': prev,
                                    'next': next,
                                    'count': count,
                                    'category': category, })
