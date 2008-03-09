from django.conf.urls.defaults import *

from sphene.sphblog.feeds import LatestBlogPosts

feeds = {
    'latestposts': LatestBlogPosts,
}

urlpatterns = patterns('sphene.sphblog.views',
                       url(r'^$', 'blogindex', name='sphblog_index'),
                       url(r'^postthread/$', 'postthread', name = 'sphblog_postthread'),
                       url(r'^tag/(?P<tag_name>\w+)/$', 'show_tag_posts', name = 'sphblog_show_tag_posts'),
                       (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>.*)/$', 'show_thread'),
                       )
urlpatterns += patterns('',
                        url(r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed',
                            { 'feed_dict': feeds,
                              'noGroup': True,
                              },
                            name = 'sphblog-feeds'),
                       )

