from django.urls import re_path

from .feeds import LatestThreads, LatestGlobalThreads
from .views import options, CategoryList, ThreadListView
from .views import move
from .views import listThreads
from .views import post
from .views import reply
from .views import annotate
from .views import hide
from .views import move_post_1
from .views import move_post_2
from .views import move_post_3
from .views import delete_moved_info
from .views import vote
from .views import toggle_monitor
from .views import catchup
from .views import edit_poll
from .views import admin_user_posts
from .views import admin_post_delete
from .views import admin_posts_delete


urlpatterns = [
    re_path(r'^feeds/latest/(?P<category_id>.+)/$',
            LatestThreads(),
            {},
            'sphboard-feeds'),
    re_path(r'^feeds/all/$',
            LatestGlobalThreads(),
            {},
            'sphboard-global-feeds')
]

urlpatterns += [
    re_path(r'^$', CategoryList.as_view(), {'category_id': None}, name='sphboard-index'),
    re_path(r'^show/(?P<category_id>\d+)/(?P<slug>.+)/$', CategoryList.as_view(), name='sphboard_show_category'),
    re_path(r'^show/(?P<category_id>\d+)/$', CategoryList.as_view(), name='sphboard_show_category_without_slug'),
    re_path(r'^list_threads/(?P<category_id>\d+)/$', listThreads, ),
    re_path(r'^latest/(?:(?P<category_id>\d*)/)?$', CategoryList.as_view(), {'show_type': 'threads'}, name='sphboard_latest'),
    re_path(r'^thread/(?P<thread_id>\d+)/(?P<slug>.+)/$', ThreadListView.as_view(), name='sphboard_show_thread'),
    re_path(r'^thread/(?P<thread_id>\d+)/$', ThreadListView.as_view(), name='sphboard_show_thread_without_slug'),
    re_path(r'^options/(?P<thread_id>\d+)/$', options, name='sphboard_options'),
    re_path(r'^move/(?P<thread_id>\d+)/$', move, name='sphboard_move_thread'),
    re_path(r'^post/(?P<category_id>\d+)/(?P<post_id>\d+)/$', post, name='sphboard-post-reply'),
    re_path(r'^post/(?P<category_id>\d+)/$', post, name='sphboard_post_thread'),
    re_path(r'^reply/(?P<category_id>\d+)/(?P<thread_id>\d+)/$', reply, name='sphboard_reply'),
    re_path(r'^annotate/(?P<post_id>\d+)/$', annotate, name='sphboard-annotate'),
    re_path(r'^hide/(?P<post_id>\d+)/$', hide, name='sphboard-hide'),
    re_path(r'^move_post_1/(?P<post_id>\d+)/$', move_post_1, name='move_post_1'),
    re_path(r'^move_post_2/(?P<post_id>\d+)/(?P<category_id>\d+)/$', move_post_2, name='move_post_2'),
    re_path(r'^move_post_3_cat/(?P<post_id>\d+)/(?P<category_id>\d+)/$', move_post_3, name='move_post_3'),
    re_path(r'^move_post_3_thr/(?P<post_id>\d+)/(?P<category_id>\d+)/(?P<thread_id>\d+)/$', move_post_3,
            name='move_post_3'),
    re_path(r'^delete_moved_info/(?P<pk>\d+)/$', delete_moved_info, name='delete_moved_info'),
    re_path(r'^vote/(?P<thread_id>\d+)/$', vote, name="vote"),
    re_path(r'^togglemonitor_(?P<monitortype>\w+)/(?P<object_id>\d+)/(?P<monitor_user_id>\d+)/$', toggle_monitor,
            name='sphboard_toggle_user_monitor'),
    re_path(r'^togglemonitor_(?P<monitortype>\w+)/(?P<object_id>\d+)/$', toggle_monitor,
            name='sphboard_toggle_monitor'),
    re_path(r'^catchup/(?P<category_id>\d+)/$', catchup, name='sphboard-catchup'),
    re_path(r'^poll/(?P<poll_id>\d+)/edit/$', edit_poll, name='sphboard_edit_poll'),
    re_path(r'^admin/(?P<user_id>\d+)/posts/$', admin_user_posts, name='sphboard_admin_user_posts'),
    re_path(r'^admin/(?P<user_id>\d+)/posts/(?P<post_id>\d+)/delete/$', admin_post_delete,
            name='sphboard_admin_post_delete'),
    re_path(r'^admin/(?P<user_id>\d+)/posts/delete/$', admin_posts_delete, name='sphboard_admin_posts_delete'),
]
