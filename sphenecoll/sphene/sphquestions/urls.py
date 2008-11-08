from django.conf.urls.defaults import *


urlpatterns = patterns( \
    'sphene.sphquestions.views',
    url(r'^vote/(?P<reply_id>\d+)/$', 'votereply', name = 'sphquestions_votereply'),
    )



