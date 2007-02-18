from django.conf import settings
from django.conf.urls.defaults import *
from django.http import Http404
from django.shortcuts import get_object_or_404
from sphene.community.models import Group
from django.core import urlresolvers

# If all are used the following order has to remain:
# 1.) ThreadLocals
# 2.) MultiHostMiddleware
# 3.) GroupMiddleware
# all other orders will lead to problems ..

class MultiHostMiddleware:
    def process_request(self, request):
        try:
            host = request.META['HTTP_HOST']
            if host[-3:] == ':80':
                host = host[:-3] # ignore default port number, if present
            urlconf = settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP[host]
            set_current_urlconf_params( urlconf['params'] )
            request.urlconf = urlconf['urlconf']
            
        except KeyError:
            pass # use default urlconf

class GroupMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.attributes = { }
        if 'urlPrefix' in view_kwargs:
            urlPrefix = view_kwargs['urlPrefix']
            if urlPrefix != '':
                urlPrefix = '/' + urlPrefix
            request.attributes['urlPrefix'] = urlPrefix
            del view_kwargs['urlPrefix']
        if 'groupName' in view_kwargs:
            groupName = view_kwargs['groupName']
            if groupName == None: groupName = get_current_urlconf_params()['groupName']
            group = get_object_or_404(Group, name = groupName )
            del view_kwargs['groupName']
            view_kwargs['group'] = group
            request.attributes['group'] = group
            #settings.TEMPLATE_DIRS = ( "/tmp/hehe", ) + settings.TEMPLATE_DIRS
        return None

# copied from http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
# threadlocals middleware
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local
    
_thread_locals = local()
def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_urlconf_params():
    return getattr(_thread_locals, 'urlconf_params', None)

def set_current_urlconf_params(urlconf_params):
    _thread_locals.urlconf_params = urlconf_params
    
class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        try:
            delattr(_thread_locals, 'urlconf_params')
        except AttributeError:
            pass
        

