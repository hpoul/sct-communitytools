import os

from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

defaultdict = { 'groupName': 'example' }

urlpatterns = patterns('',
    (r'^community/', include('sphene.community.urls'), defaultdict),
    (r'^board/', include('sphene.sphboard.urls'), defaultdict),
    (r'^wiki/', include('sphene.sphwiki.urls'), defaultdict),

    (r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    urlpatterns += patterns('',
          (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': os.path.join(os.path.dirname(__file__), 'media/')})
          )