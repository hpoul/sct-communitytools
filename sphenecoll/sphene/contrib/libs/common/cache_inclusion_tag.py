#
# This code was copied from
#  http://axiak.net/blog/2007/5/22/cached-inclusion-tag/
# Originally written by Michael C Axiak (obvioulsy)
#
# (As of time of this writing .. the site was not available.. i have to access
#  it through google cache :) )
#
#
import functools

from django.core.cache import cache
from django import template
from django.template.base import Template
from django.template.library import TagHelperNode, parse_bits
from inspect import getfullargspec
from django.utils.itercompat import is_iterable

__all__ = ['cache_inclusion_tag']


def cache_inclusion_tag(self, filename, cache_key_func=None, cache_time=99999, context_class=template.Context,
                        takes_context=False, name=None):
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
        params, varargs, varkw, defaults, kwonly, kwonly_defaults, _ = getfullargspec(func)
        function_name = (name or getattr(func, '_decorated_function', func).__name__)

        class InclusionNode(TagHelperNode):
            def render(self, context):
                """
                Render the specified template and context. Cache the template object
                in render_context to avoid reparsing and loading when used in a for
                loop.
                """
                resolved_args, resolved_kwargs = self.get_resolved_arguments(context)

                if takes_context:
                    args = [context] + resolved_args
                else:
                    args = resolved_args
                if cache_key_func:
                    cache_key = cache_key_func(*args)
                else:
                    cache_key = None

                if cache_key is not None:
                    ret_val = cache.get(cache_key)
                    if ret_val:
                        return ret_val

                _dict = self.func(*resolved_args, **resolved_kwargs)

                t = context.render_context.get(self)
                if t is None:
                    if isinstance(self.filename, Template):
                        t = self.filename
                    elif isinstance(getattr(self.filename, 'template', None), Template):
                        t = self.filename.template
                    elif not isinstance(self.filename, str) and is_iterable(self.filename):
                        t = context.template.engine.select_template(self.filename)
                    else:
                        t = context.template.engine.get_template(self.filename)
                    context.render_context[self] = t
                new_context = context.new(_dict)
                # Copy across the CSRF token, if present, because inclusion tags are
                # often used for forms, and we need instructions for using CSRF
                # protection to be as simple as possible.
                csrf_token = context.get('csrf_token')
                if csrf_token is not None:
                    new_context['csrf_token'] = csrf_token
                ret_val = t.render(new_context)
                if cache_key is not None:
                    cache.set(cache_key, ret_val, cache_time)
                return ret_val

        @functools.wraps(func)
        def compile_func(parser, token):
            bits = token.split_contents()[1:]
            args, kwargs = parse_bits(
                parser, bits, params, varargs, varkw, defaults,
                kwonly, kwonly_defaults, takes_context, function_name,
            )
            return InclusionNode(
                func, takes_context, args, kwargs, filename,
            )
        self.tag(function_name, compile_func)
        return func
    return dec
