from django.conf.urls.defaults import *

from sphene.sphblog.feeds import LatestBlogPosts

#feeds = {
#    'latestposts': LatestBlogPosts,
#}

urlpatterns = patterns('',
        url(r'^feeds/latestposts/$', LatestBlogPosts(),
                            { 
                              'noGroup': True,
                              },
                            name = 'sphblog-feeds'),
        url(r'^feeds/latestposts/(?P<category_id>\d+)/$', LatestBlogPosts(),
                            { 
                              'noGroup': True,
                              },
                            name = 'sphblog-feeds'),
                       )
urlpatterns += patterns('sphene.sphblog.views',
                       url(r'^$', 'blogindex', name='sphblog_index'),
                       url(r'^postthread/$', 'postthread', name = 'sphblog_postthread'),
                       url(r'^tag/(?P<tag_name>\w+)/(?:page/(?P<page>\d+)/)?$', 'show_tag_posts', name = 'sphblog_show_tag_posts'),

                       # Indexes for year and month based archive
                       url(r'^archive/(?P<year>\d{4})/$', 'blogindex', name='sphblog_archive_year'),
                       url(r'^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'blogindex', name='sphblog_archive_month'),
                       # Paged archives
                       url(r'^archive/(?P<year>\d{4})/page/(?P<page>\d+)/$', 'blogindex', name='sphblog_archive_year_paged'),
                       url(r'^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/page/(?P<page>\d+)/$', 'blogindex', name='sphblog_archive_month_paged'),

                       url(r'^page/(?P<page>\d+)/$', 'blogindex', name='sphblog_paged_index'),

                       (r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>.*)/$', 'show_thread_redirect'),
                       url(r'^(?P<category_id>\d+)/$', 'blogindex_redirect', name='sphblog_category_index'),
                       url(r'^(?P<category_slug>[\w\-]+)/$', 'blogindex', name='sphblog_category_index_slug'),
                       (r'^(?P<category_slug>[\w\-]+?)/(?P<slug>[\w\-]+)/$', 'show_thread'),
                       )

