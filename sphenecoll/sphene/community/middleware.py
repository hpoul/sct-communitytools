from django.conf import settings
from django.conf.urls.defaults import *
from django.http import Http404
from django.shortcuts import get_object_or_404
from sphene.community.models import Group
from django.core import urlresolvers
import re

from django.contrib.sites.models import SiteManager, Site

def my_get_current(self):
    group = get_current_group()
    if not group:
        from django.conf import settings
        return self.get(pk=settings.SITE_ID)
    else:
        return Site( domain = group.baseurl, name = group.name )

SiteManager.get_current = my_get_current
                    


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
            urlconf = None
            urlconf_params = None
            if host in settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP:
                urlconf = settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP[host]
            else:
                # TODO cache results ? - cache regular expressions .. ?
                for key, value in settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP.iteritems():
                    regex = re.compile(key)
                    match = regex.match(host)
                    if not match:
                        continue
                    # We got a match.
                    urlconf = value
                    urlconf_params = 'params' in urlconf and urlconf['params'].copy() or dict()
                    namedgroups = match.groupdict()
                    for key, value in namedgroups.iteritems():
                        urlconf_params[key] = value
                    break
            if not urlconf:
                print "Unable to find urlconf !!!"
                return
            while 'alias' in urlconf:
                urlconf = settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP[urlconf['alias']]
            set_current_urlconf_params( urlconf_params or urlconf['params'] )
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
        group = None
        groupName = None
        if get_current_urlconf_params() and 'groupName' in get_current_urlconf_params():
            groupName = get_current_urlconf_params()['groupName']
            group = get_object_or_404(Group, name = groupName)
        if 'groupName' in view_kwargs:
            groupName = view_kwargs['groupName']
            if groupName == None: groupName = get_current_urlconf_params()['groupName']
            if group == None:
                group = get_object_or_404(Group, name = groupName )
            del view_kwargs['groupName']
            view_kwargs['group'] = group
            request.attributes['group'] = group
            #settings.TEMPLATE_DIRS = ( "/tmp/hehe", ) + settings.TEMPLATE_DIRS
        set_current_group( group )
        return None

# copied from http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
# threadlocals middleware
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

print "Executing module body."
_thread_locals = local()
def get_current_request():
    return getattr(_thread_locals, 'request', None)

def get_current_session():
    req = get_current_request()
    if req == None: return None
    return req.session

def get_current_user():
    user = getattr(_thread_locals, 'user', None)
    if user != None: return user
    req = get_current_request()
    if req == None: return None
    return req.user

def get_current_group():
    return getattr(_thread_locals, 'group', None)

def get_current_urlconf_params():
    return getattr(_thread_locals, 'urlconf_params', None)

def set_current_urlconf_params(urlconf_params):
    _thread_locals.urlconf_params = urlconf_params

def set_current_group(group):
    _thread_locals.group = group

def get_current_sphdata():
    return getattr(_thread_locals, 'sphdata', None)
    
class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.sphdata = { }
        try:
            delattr(_thread_locals, 'urlconf_params')
        except AttributeError:
            pass
        _thread_locals.group = None
        



## copied from http://code.djangoproject.com/wiki/PageStatsMiddleware
import re
from operator import add
from time import time
from django.db import connection

class StatsMiddleware(object):

    def process_view(self, request, view_func, view_args, view_kwargs):

        # turn on debugging in db backend to capture time
        from django.conf import settings
        debug = settings.DEBUG
        settings.DEBUG = True

        # get number of db queries before we do anything
        n = len(connection.queries)

        # time the view
        start = time()
        response = view_func(request, *view_args, **view_kwargs)
        totTime = time() - start

        # compute the db time for the queries just run
        queries = len(connection.queries) - n
        if queries:
            dbTime = reduce(add, [float(q['time']) 
                                  for q in connection.queries[n:]])
        else:
            dbTime = 0.0

        # and backout python time
        pyTime = totTime - dbTime

        # restore debugging setting
        settings.DEBUG = debug

        stats = {
            'totTime': totTime,
            'pyTime': pyTime,
            'dbTime': dbTime,
            'queries': queries,
            }

        # replace the comment if found            
        if response and response.content:
            s = response.content
            regexp = re.compile(r'(?P<cmt><!--\s*STATS:(?P<fmt>.*?)-->)')
            match = regexp.search(s)
            if match:
                s = s[:match.start('cmt')] + \
                    match.group('fmt') % stats + \
                    s[match.end('cmt'):]
                response.content = s

        return response

from django.core.handlers.modpython import ModPythonRequest

class ModPythonSetLoggedinUser(object):
    def process_request(self, request):
        if not isinstance(request, ModPythonRequest):
            return None

        if not hasattr(request, '_req'):
            return None

        if not hasattr(request, 'user') or not request.user.is_authenticated():
            return None

        request._req.user = request.user.username

        return None


class PsycoMiddleware(object):
    def process_request(self, request):
        import psyco
	psyco.profile()
	return None

from sphene.community import PermissionDenied
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.template import loader
from django.http import HttpResponseForbidden
class PermissionDeniedMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return HttpResponseForbidden(loader.render_to_string( 'sphene/community/permissiondenied.html',
                                                                  { 'exception': exception,
                                                                    },
                                                                  context_instance = RequestContext(request) ) )
        return None
