import datetime

from django import template
from django.template.context import Context

from sphene.sphblog.views import get_posts_queryset

register = template.Library()


@register.inclusion_tag('sphene/sphblog/_showblogpost.html', takes_context = True)
def sphblog_showblogpost(context, post):
    ret = {'post': post,
           'blogpost': post.blogpostextension_set.get(),
           }
    retctx = Context(context)
    retctx.update(ret)
    return retctx

@register.inclusion_tag('sphene/sphblog/_showarchivelinks.html', takes_context = True)
def show_archive(context):
    # There has to be a better way of getting the posts
    # which does not involve passing data in the context
    threads = get_posts_queryset(context['group'], context['categories'])
    # Get dates
    threads = threads.values('postdate')
    # Make unique (year, month) tuple list
    months = list(set([(t['postdate'].year, t['postdate'].month) for t in threads]))
    # Sort it by year and then by month, in increasing order (last month first)
    months = sorted(months, lambda a, b: cmp(a[0], b[0]) or cmp(a[1], b[1]))
    months.reverse()
    return {'links': months}

@register.filter(name='humanize_month')
def humanize_month(value):
    try:
        return datetime.date(1900, int(value), 1).strftime('%B')
    except ValueError:
        return ''

