from django import template
from django.template.context import Context


register = template.Library()


@register.inclusion_tag('sphene/sphblog/_showblogpost.html', takes_context = True)
def sphblog_showblogpost(context, post):
    ret = {'post': post,
           'blogpost': post.blogpostextension_set.get(),
           }
    retctx = Context(context)
    retctx.update(ret)
    return retctx
