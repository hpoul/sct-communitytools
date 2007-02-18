from django.conf.urls.defaults import *

from django.conf.urls.defaults import *


urlpatterns = patterns('',
                       (r'^$', 'django.views.generic.simple.redirect_to', {'url': 'show/0/'}),
                       )
urlpatterns += patterns('sphene.sphboard.views',
                        (r'^show/(?P<category_id>\d+)/$', 'showCategory'),
                        (r'^latest/(?P<category_id>\d+)/$', 'showCategory', { 'showType': 'threads' }),
                        (r'^thread/(?P<thread_id>\d+)/$', 'showThread'),
                        (r'^options/(?P<thread_id>\d+)/$', 'options'),
                        (r'^post/(?P<category_id>\d+)/$', 'post'),
                        (r'^vote/(?P<thread_id>\d+)/$', 'vote'),
                       )

