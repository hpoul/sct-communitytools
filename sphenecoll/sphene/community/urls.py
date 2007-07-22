from django.conf.urls.defaults import *



urlpatterns = patterns('',
                       (r'captcha/(?P<token_id>\w+).jpg$', 'sphene.community.views.captcha_image'),
                       #(r'accounts/login/$', 'django.contrib.auth.views.login', { 'noGroup': True,
                       #                                                           }),
                       #(r'accounts/register/$', 'django.contrib.auth.views.logout', { 'noGroup': True,
                       #                                                               }),
                       )

urlpatterns += patterns( 'sphene.community.views',
                         (r'accounts/login/$', 'accounts_login'),
                         (r'accounts/logout/$', 'accounts_logout'),
                         (r'accounts/forgot/$', 'accounts_forgot'),
                         (r'profile/(?P<user_id>\d+)/$', 'profile'),
                         (r'profile/edit/$', 'profile_edit_mine'),
                         (r'profile/edit/(?P<user_id>\d+)/$', 'profile_edit'),
                         )
