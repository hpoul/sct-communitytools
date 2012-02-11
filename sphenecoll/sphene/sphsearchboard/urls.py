from django.conf.urls.defaults import *


urlpatterns = patterns('sphene.sphsearchboard.views',
                       url(r'^$', 'view_search_posts', name = 'sphsearchboard_posts'),)
try:
    from djapian import load_indexes
    load_indexes()
except:
    pass
