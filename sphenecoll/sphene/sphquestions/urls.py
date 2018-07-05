from django.urls import re_path

from .views import votereply

urlpatterns = [
    re_path(r'^vote/(?P<reply_id>\d+)/$', votereply, name='sphquestions_votereply'),
]
