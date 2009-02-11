import datetime

from django import template
from django.template.context import Context

from sphene.community.middleware import get_current_group

from sphene.sphblog.views import get_posts_queryset, get_board_categories

register = template.Library()


@register.inclusion_tag('sphene/sphblog/_showblogpost.html', takes_context = True)
def sphblog_showblogpost(context, post):
    ret = {'post': post,
           'blogpost': post.blogpostextension_set.get(),
           }
    retctx = Context(context)
    retctx.update(ret)
    return retctx

@register.inclusion_tag('sphene/sphblog/_showarchivelinks.html')
def show_archive(categories = None):
    group = get_current_group()
    if categories is None:
        categories = get_board_categories(group)
    threads = get_posts_queryset(group, categories)
    # Get dates
    threads = threads.values('postdate')
    # Count posts in (year, month) tuples
    months_dict = dict()
    for t in threads:
        tmp = (t['postdate'].year, t['postdate'].month)
        months_dict[tmp] = months_dict.get(tmp, 0) + 1

    # Sort it by year and then by month, in increasing order (last month first)
    months = sorted(months_dict.iteritems(), \
                        lambda a, b: \
                        cmp(a[0][0], b[0][0]) \
                        or cmp(a[0][1], b[0][1]))
    months.reverse()
    return {'links': months}

@register.filter(name='humanize_month')
def humanize_month(value):
    try:
        return datetime.date(1900, int(value), 1).strftime('%B')
    except ValueError:
        return ''

