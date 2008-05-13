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
                print "Unable to find urlconf for %s / map: %s !!!" % (host, str(settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP))
                return
            while 'alias' in urlconf:
                urlconf = settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP[urlconf['alias']]
                
            myparams = urlconf_params or urlconf['params']

            # if there is a parameter called 'groupName', load the given group,
            # and set it into the thread locals.
            if myparams and 'groupName' in myparams:
                try:
                    set_current_group( Group.objects.get( name__exact = myparams['groupName'] ) )
                except Group.DoesNotExist:
                    pass
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
            # Check if we already loaded the current group in another
            # middleware.
            group = get_current_group()
            if group is None or group.name != groupName:
                group = get_object_or_404(Group, name = groupName)
        if 'groupName' in view_kwargs:
            if view_kwargs.get( 'noGroup', False ):
                del view_kwargs['groupName']
                del view_kwargs['noGroup']
            else:
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

#print "Executing module body."
_thread_locals = local()
def get_current_request():
    return getattr(_thread_locals, 'request', None)

def get_current_urlconf():
    return getattr(get_current_request(), 'urlconf', None)

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
import logging

logger = logging.getLogger('sphene.community.middleware')

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
        response = None
        try:
            response = view_func(request, *view_args, **view_kwargs)
        finally:
            if request.path.startswith('/static'):
                return response

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
                    out = match.group('fmt') % stats
                    #for query in connection.queries:
                    #    logger.debug( '  %5s : %s' % (query['time'], query['sql'], ) )
                    response.content = s

            querystr = ''
            for query in connection.queries:
                sql = query['sql']
                if sql is None: sql = " ?WTF?None?WTF? "
                querystr += "\t" + query['time'] + "\t" + sql + "\n"
            logger.debug( 'All Queries: %s' % (querystr,) )
            logger.info( 'Request %s: %s' % (request.get_full_path(), stats,) )

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

	# request.user.username is a unicode string
	# but _req.user requires an ascii string (afaik)
        request._req.user = str(request.user.username)

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



class LastModified(object):
    """ Middleware that sets the Last-Modified and associated headers,
    if requested by the view. (By setting the sph_lastmodified attribute
    of the response object.

    based on a contribution of Andrew Plotkin:
    http://eblong.com/zarf/boodler/sitework/
    """

    def process_response(self, request, response):
        stamp = getattr(response, 'sph_lastmodified', None)
        if not stamp: return response

        import rfc822
        import calendar
        if stamp is True:
            val = rfc822.formatdate()
        else:
            val = rfc822.formatdate(calendar.timegm(stamp.timetuple()))
        response['Last-Modified'] = val
        response['Cache-Control'] = 'private, must-revalidate, max-age=0'
        return response

