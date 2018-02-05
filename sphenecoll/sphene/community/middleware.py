import re
from functools import reduce
from operator import add
from time import time
import logging
# copied from http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser
# threadlocals middleware
from threading import local

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.contrib.sites.models import SiteManager, Site
from django.db import connection
from django.http import HttpResponseForbidden

from sphene.community import PermissionDenied
from sphene.community.models import Group
from sphene.community.sphsettings import get_sph_setting

logger = logging.getLogger('sphene.community.middleware')
# print "Executing module body."
_thread_locals = local()


def my_get_current(self):
    try:
        group = get_current_group()
    except AttributeError as e:
        group = None
    if not group:
        return self.get(pk=settings.SITE_ID)
    else:
        return Site(pk=settings.SITE_ID, domain=group.baseurl, name=group.name)


SiteManager.get_current = my_get_current


# If all are used the following order has to remain:
# 1.) ThreadLocals (required)
# 2.) MultiHostMiddleware (optional, but very much recommended!)
# 3.) GroupMiddleware (required)
# all other orders will lead to problems ..


#
# Short descriptions:
#  every module within SCT requires a Group object - this can either come from the
#  MultiHostMiddleware - ie. from the domain/host name (vhosts) or from an URL parameter.
#  we need to somehow distuingish between those two within the reverse URL lookups.
#

class MultiHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            sphdata = get_current_sphdata()
            host = request.META['HTTP_HOST']
            if host[-3:] == ':80':
                host = host[:-3]  # ignore default port number, if present
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
                    for ng_key, ng_value in namedgroups.items():
                        urlconf_params[ng_key] = ng_value
                    break
            if not urlconf:
                logging.info("Unable to find urlconf for %s / map: %s !!!" % (
                    host, str(settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP)))
                return
            while 'alias' in urlconf:
                urlconf = settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP[urlconf['alias']]

            myparams = urlconf_params or urlconf['params']

            # if there is a parameter called 'groupName', load the given group,
            # and set it into the thread locals.
            if myparams and 'groupName' in myparams:
                try:
                    set_current_group(Group.objects.get(name__exact=myparams['groupName']))
                    sphdata['group_fromhost'] = True
                except Group.DoesNotExist:
                    pass
            set_current_urlconf_params(urlconf_params or urlconf['params'])
            request.urlconf = urlconf['urlconf']

        except KeyError:
            pass  # use default urlconf

        response = self.get_response(request)
        return response


class GroupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        request.attributes = {}
        if 'urlPrefix' in view_kwargs:
            url_prefix = view_kwargs['urlPrefix']
            if url_prefix != '':
                url_prefix = '/' + url_prefix
            request.attributes['urlPrefix'] = url_prefix
            del view_kwargs['urlPrefix']
        group = None
        group_name = None
        if get_current_urlconf_params() and 'groupName' in get_current_urlconf_params():
            group_name = get_current_urlconf_params()['groupName']
            # Check if we already loaded the current group in another
            # middleware.
            group = get_current_group()
            if group is None or group.name != group_name:
                try:
                    group = get_object_or_404(Group, name=group_name)
                except Http404 as e:
                    # We allow access to admin site without group.
                    if not view_func.__module__.startswith('django.contrib.admin.'):
                        raise e
        if 'groupName' in view_kwargs:
            if view_kwargs.get('noGroup', False):
                del view_kwargs['groupName']
                del view_kwargs['noGroup']
            else:
                group_name = view_kwargs['groupName']
                if group_name is None:
                    group_name = get_current_urlconf_params()['groupName']
                sphdata = get_current_sphdata()
                if group is None:
                    group = get_object_or_404(Group, name=group_name)
                    sphdata['group_fromhost'] = not get_sph_setting('community_groups_in_url')
                del view_kwargs['groupName']
                view_kwargs['group'] = group
                request.attributes['group'] = group
                # settings.TEMPLATE_DIRS = ( "/tmp/hehe", ) + settings.TEMPLATE_DIRS

        set_current_group(group)
        return None


def get_current_request():
    return getattr(_thread_locals, 'request', None)


def get_current_urlconf():
    return getattr(get_current_request(), 'urlconf', None)


def get_current_session():
    req = get_current_request()
    if req is None:
        return None
    return req.session


def get_current_user():
    user = getattr(_thread_locals, 'user', None)
    if user is not None:
        return user
    req = get_current_request()
    if req is None:
        return None
    return req.user


def get_current_group():
    try:
        return _thread_locals.group
    except AttributeError as e:
        logger.error('Unable to retrieve group. Is GroupMiddleware enabled?')
        raise e


def get_current_urlconf_params():
    return getattr(_thread_locals, 'urlconf_params', None)


def set_current_urlconf_params(urlconf_params):
    _thread_locals.urlconf_params = urlconf_params


def set_current_group(group):
    _thread_locals.group = group


def get_current_sphdata():
    return getattr(_thread_locals, 'sphdata', None)


class ThreadLocals:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.sphdata = {}
        try:
            delattr(_thread_locals, 'urlconf_params')
        except AttributeError:
            pass
        _thread_locals.group = None

        response = self.get_response(request)
        return response


# copied from http://code.djangoproject.com/wiki/PageStatsMiddleware
class StatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

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

            tot_time = time() - start

            # compute the db time for the queries just run
            queries = len(connection.queries) - n
            if queries:
                db_time = reduce(add, [float(q['time'])
                                       for q in connection.queries[n:]])
            else:
                db_time = 0.0

            # and backout python time
            py_time = tot_time - db_time

            # restore debugging setting
            settings.DEBUG = debug

            stats = {
                'totTime': tot_time,
                'pyTime': py_time,
                'dbTime': db_time,
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
                    # for query in connection.queries:
                    #    logger.debug( '  %5s : %s' % (query['time'], query['sql'], ) )
                    response.content = s

            querystr = ''
            for query in connection.queries:
                sql = query['sql']
                if sql is None: sql = " ?WTF?None?WTF? "
                querystr += "\t" + query['time'] + "\t" + sql + "\n"
            logger.debug('All Queries: %s' % (querystr,))
            logger.info('Request %s: %s' % (request.get_full_path(), stats,))

        return response


class PermissionDeniedMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return HttpResponseForbidden(
                render(
                    request,
                    'sphene/community/permissiondenied.html',
                    {'exception': exception}
                )
            )
        return None
