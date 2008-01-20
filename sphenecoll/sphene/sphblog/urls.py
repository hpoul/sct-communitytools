from django.conf.urls.defaults import *

from sphene.sphblog.feeds import LatestBlogPosts

feeds = {
    'latestposts': LatestBlogPosts,
}

urlpatterns = patterns('sphene.sphblog.views',
                       (r'^$', 'blogindex'),
                       url(r'^postthread/$', 'postthread', name = 'sphblog_postthread'),
                       (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>.*)/$', 'show_thread'),
                       )
urlpatterns += patterns('',
                        url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
                            { 'feed_dict': feeds,
                              'noGroup': True,
                              },
                            name = 'sphblog-feeds'),
                       )

