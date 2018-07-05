from django.urls import re_path

from sphene.sphblog.feeds import LatestBlogPosts
from .views import blogindex
from .views import postthread
from .views import show_tag_posts
from .views import show_thread_redirect
from .views import blogindex_redirect
from .views import show_thread


urlpatterns = [
    re_path(r'^feeds/latestposts/$',
            LatestBlogPosts(),
            {
                'noGroup': True
            },
            name='sphblog-feeds'),
    re_path(r'^feeds/latestposts/(?P<category_id>\d+)/$',
            LatestBlogPosts(),
            {
                'noGroup': True
            },
            name='sphblog-feeds'),
    re_path(r'^$', blogindex, name='sphblog_index'),
    re_path(r'^postthread/$', postthread, name='sphblog_postthread'),
    re_path(r'^tag/(?P<tag_name>\w+)/(?:page/(?P<page>\d+)/)?$',
            show_tag_posts,
            name='sphblog_show_tag_posts'),

    # Indices for year and month based archive
    re_path(r'^archive/(?P<year>\d{4})/$', blogindex, name='sphblog_archive_year'),
    re_path(r'^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/$', blogindex,
            name='sphblog_archive_month'),
    # Paged archives
    re_path(r'^archive/(?P<year>\d{4})/page/(?P<page>\d+)/$', blogindex,
            name='sphblog_archive_year_paged'),
    re_path(r'^archive/(?P<year>\d{4})/(?P<month>\d{1,2})/page/(?P<page>\d+)/$', blogindex,
            name='sphblog_archive_month_paged'),

    re_path(r'^page/(?P<page>\d+)/$', blogindex, name='sphblog_paged_index'),

    re_path(r'^(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/(?P<slug>.*)/$', show_thread_redirect),
    re_path(r'^(?P<category_id>\d+)/$', blogindex_redirect, name='sphblog_category_index'),
    re_path(r'^(?P<category_slug>[\w\-]+)/$', blogindex, name='sphblog_category_index_slug'),
    re_path(r'^(?P<category_slug>[\w\-]+?)/(?P<slug>[\w\-]+)/$', show_thread),
]
