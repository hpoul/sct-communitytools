#
# This code was copied from
#  http://axiak.net/blog/2007/5/22/cached-inclusion-tag/
# Originally written by Michael C Axiak (obvioulsy)
#
# (As of time of this writing .. the site was not available.. i have to access
#  it through google cache :) )
#
#
from functools import partial

from django.core.cache import cache
from django import template
from django.template.base import TagHelperNode, Template, generic_tag_compiler
from django.utils.functional import curry
from inspect import getargspec
from django.utils.itercompat import is_iterable

__all__ = ['cache_inclusion_tag']

def cache_inclusion_tag(self, file_name, cache_key_func=None, cache_time=99999, context_class=template.Context,  takes_context=False, name=None):
    """
    This function will cache the rendering and output of a inclusion tag for cache_time seconds.

    To use, just do the following::

    from django import template
    from esp.web.util.template import cache_inclusion_tag
    
    register = template.Library()

    def cache_key_func(foo, bar, baz):
        # takes the same arguments as below
        return str(foo)

    @cache_inclusion_tag(register, 'path/to/template.html', cache_key_func=cache_key_func)
    def fun_tag(foo, bar, baz):
        return {'foo': foo}


    The tag will now be cached.
    """
    def dec(func):
        params, varargs, varkw, defaults = getargspec(func)

        class InclusionNode(TagHelperNode):
            def render(self, context):
                resolved_args, resolved_kwargs = self.get_resolved_arguments(context)

                if takes_context:
                    args = [context] + resolved_args
                else:
                    args = resolved_args

                if cache_key_func:
                    cache_key = cache_key_func(*args)
                else:
                    cache_key = None

                if cache_key != None:
                    retVal = cache.get(cache_key)
                    if retVal:
                        return retVal

                _dict = func(*resolved_args, **resolved_kwargs)

                if not getattr(self, 'nodelist', False):
                    from django.template.loader import get_template, select_template
                    if isinstance(file_name, Template):
                        t = file_name
                    elif not isinstance(file_name, basestring) and is_iterable(file_name):
                        t = select_template(file_name)
                    else:
                        t = get_template(file_name)
                    self.nodelist = t.nodelist
                new_context = context_class(_dict, **{
                    'autoescape': context.autoescape,
                    'current_app': context.current_app,
                    'use_l10n': context.use_l10n,
                    'use_tz': context.use_tz,
                })
                # Copy across the CSRF token, if present, because
                # inclusion tags are often used for forms, and we need
                # instructions for using CSRF protection to be as simple
                # as possible.
                csrf_token = context.get('csrf_token', None)
                if csrf_token is not None:
                    new_context['csrf_token'] = csrf_token

                retVal = self.nodelist.render(new_context)
                if cache_key != None:
                    cache.set(cache_key, retVal, cache_time)
                return retVal

        function_name = (name or
            getattr(func, '_decorated_function', func).__name__)
        compile_func = partial(generic_tag_compiler,
            params=params, varargs=varargs, varkw=varkw,
            defaults=defaults, name=function_name,
            takes_context=takes_context, node_class=InclusionNode)
        compile_func.__doc__ = func.__doc__
        self.tag(function_name, compile_func)
        return func

    return dec
