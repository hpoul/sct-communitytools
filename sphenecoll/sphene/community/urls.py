from django.conf.urls.defaults import *



urlpatterns = patterns('',
                       (r'captcha/(?P<token_id>\w+).jpg$', 'sphene.community.views.captcha_image'),
                       )
