from django.conf.urls.defaults import *

from sphene.sphboard.feeds import LatestThreads

feeds = {
    'latest': LatestThreads,
    }

urlpatterns = patterns('',
                       #url(r'^$', 'django.views.generic.simple.redirect_to', {'url': 'show/0/'}, name = 'sphboard-index'),
                       url(r'^feeds/(?P<url>.+)/$', 'django.contrib.syndication.views.feed',
                           { 'feed_dict': feeds,
                             'noGroup': True, },
                           'sphboard-feeds'),
                       )
urlpatterns += patterns('sphene.sphboard.views',
                        url(r'^$', 'showCategory', {'category_id': '0'}, name = 'sphboard-index'),
                        url(r'^show/(?P<category_id>\d+)/(?P<slug>.+)/$', 'showCategory', name = 'sphboard_show_category'),
                        url(r'^show/(?P<category_id>\d+)/$', 'showCategory', name = 'sphboard_show_category_without_slug'),
                        url(r'^list_threads/(?P<category_id>\d+)/$', 'listThreads', ),
                        url(r'^latest/(?P<category_id>\d+)/$', 'showCategory', { 'showType': 'threads' }, name = 'sphboard_latest'),
                        url(r'^thread/(?P<thread_id>\d+)/(?P<slug>.+)/$', 'showThread', name = 'sphboard_show_thread'),
                        url(r'^thread/(?P<thread_id>\d+)/$', 'showThread', name = 'sphboard_show_thread_without_slug'),
                        (r'^options/(?P<thread_id>\d+)/$', 'options'),
                        (r'^move/(?P<thread_id>\d+)/$', 'move'),
                        (r'^post/(?P<category_id>\d+)/(?P<post_id>\d+)/$', 'post'),
                        url(r'^post/(?P<category_id>\d+)/$', 'post', name = 'sphboard_post_thread'),
                        url(r'^reply/(?P<category_id>\d+)/(?P<thread_id>\d+)/$', 'reply', name = 'sphboard_reply'),
                        (r'^annotate/(?P<post_id>\d+)/$', 'annotate'),
                        (r'^vote/(?P<thread_id>\d+)/$', 'vote'),
                        (r'^togglemonitor_(?P<monitortype>\w+)/(?P<object_id>\d+)/$', 'toggle_monitor'),
                        (r'^catchup/(?P<category_id>\d+)/$', 'catchup'),
                        url(r'^poll/(?P<poll_id>\d+)/edit/$', 'edit_poll', name = 'sphboard_edit_poll'),
                       )

