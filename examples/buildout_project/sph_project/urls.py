import os

from django.conf import settings
from django.urls import re_path
from django.urls import include
from django.contrib import admin
from django.contrib.staticfiles import views

defaultdict = {'groupName': 'example'}

urlpatterns = [
    re_path(r'^community/', include('sphene.community.urls'), defaultdict),
    re_path(r'^board/', include('sphene.sphboard.urls'), defaultdict),
    re_path(r'^wiki/', include('sphene.sphwiki.urls'), defaultdict),

    re_path(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', views.serve,
                {'document_root': os.path.join(os.path.dirname(__file__), 'media/')})
    ]
