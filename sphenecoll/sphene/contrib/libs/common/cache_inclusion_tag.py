#
# This code was copied from
#  http://axiak.net/blog/2007/5/22/cached-inclusion-tag/
# Originally written by Michael C Axiak (obvioulsy)
#
# (As of time of this writing .. the site was not available.. i have to access
#  it through google cache :) )
#
# 


from django.core.cache import cache
from django import template
from django.utils.functional import curry
from inspect import getargspec

__all__ = ['cache_inclusion_tag']

def cache_inclusion_tag(register, file_name, cache_key_func=None, cache_time=99999, context_class=template.Context,  takes_context=False):
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
        params, xx, xxx, defaults = getargspec(func)
        if takes_context:
            if params[0] == 'context':
                params = params[1:]
            else:
                raise TemplateSyntaxError, "Any tag function decorated with takes_context=True must have a first argument of 'context'"

        class InclusionNode(template.Node):
            #def __init__(self, vars_to_resolve):
            #    self.vars_to_resolve = vars_to_resolve
            def __init__(self, takes_context, args, kwargs):
                self.takes_context = takes_context
                self.args = args
                self.kwargs = kwargs

            def render(self, context):
                resolved_vars = [var.resolve(context) for var in self.args]
                #for var in self.vars_to_resolve:
                #    try:
                #        resolved_vars.append(template.resolve_variable(var, context))
                #    except:
                #        resolved_vars.append(None)

                if takes_context:
                    args = [context] + resolved_vars
                else:
                    args = resolved_vars

                if cache_key_func:
                    cache_key = cache_key_func(*args)
                else:
                    cache_key = None

                if cache_key != None:
                    retVal = cache.get(cache_key)
                    if retVal:
                        return retVal

                dict = func(*args)

                if not getattr(self, 'nodelist', False):
                    from django.template.loader import get_template, select_template
                    if hasattr(file_name, '__iter__'):
                        t = select_template(file_name)
                    else:
                        t = get_template(file_name)
                    self.nodelist = t.nodelist
                retVal = self.nodelist.render(context_class(dict))
                if cache_key != None:
                    cache.set(cache_key, retVal, cache_time)
                return retVal

        compile_func = curry(template.generic_tag_compiler, params=params, varargs=None, varkw=None, defaults=defaults, name=func.__name__, node_class=InclusionNode,takes_context=takes_context)
        compile_func.__doc__ = func.__doc__
        register.tag(func.__name__, compile_func)
        return func
    return dec
