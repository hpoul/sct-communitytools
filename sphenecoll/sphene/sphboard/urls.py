from django.conf.urls.defaults import *

from sphene.sphboard.feeds import LatestThreads

feeds = {
    'latest': LatestThreads,
    }

urlpatterns = patterns('',
                       (r'^$', 'django.views.generic.simple.redirect_to', {'url': 'show/0/'}),
                       (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', { 'feed_dict': feeds,
                                                                                            'noGroup': True, }),
                       )
urlpatterns += patterns('sphene.sphboard.views',
                        (r'^show/(?P<category_id>\d+)/$', 'showCategory'),
                        (r'^latest/(?P<category_id>\d+)/$', 'showCategory', { 'showType': 'threads' }),
                        (r'^thread/(?P<thread_id>\d+)/$', 'showThread'),
                        (r'^options/(?P<thread_id>\d+)/$', 'options'),
                        (r'^post/(?P<category_id>\d+)/(?P<post_id>\d+)/$', 'post'),
                        (r'^post/(?P<category_id>\d+)/$', 'post'),
                        (r'^vote/(?P<thread_id>\d+)/$', 'vote'),
                        (r'^togglemonitor_(?P<monitortype>\w+)/(?P<object_id>\d+)/$', 'toggle_monitor'),
                        (r'^catchup/(?P<category_id>\d+)/$', 'catchup'),
                       )

