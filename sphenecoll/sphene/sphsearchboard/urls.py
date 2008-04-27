from django.conf.urls.defaults import *


urlpatterns = patterns('sphene.sphsearchboard.views',
                       url(r'^$', 'view_search_posts', name = 'sphsearchboard_posts'),)
