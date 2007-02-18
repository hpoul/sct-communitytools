from django.conf import settings
from django.conf.urls.defaults import *
from django.http import Http404
from django.shortcuts import get_object_or_404
from sphene.community.models import Group
from django.core import urlresolvers

class MultiHostMiddleware:
    def process_request(self, request):
        try:
            host = request.META['HTTP_HOST']
            if host[-3:] == ':80':
                host = host[:-3] # ignore default port number, if present
            urlconf = settings.SPH_HOST_MIDDLEWARE_URLCONF_MAP[host]
            request.urlconf = urlconf
            
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
            group = get_object_or_404(Group, name = view_kwargs['groupName'] )
            del view_kwargs['groupName']
            view_kwargs['group'] = group
            request.attributes['group'] = group
            #settings.TEMPLATE_DIRS = ( "/tmp/hehe", ) + settings.TEMPLATE_DIRS
        return None

