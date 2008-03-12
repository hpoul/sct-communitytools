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

                         url(r'admin/permission/role/list/$', 'admin_permission_role_list', name = 'community_admin_permission_role_list'),
                         url(r'admin/permission/role/edit/(?P<role_id>\d+)/$', 'admin_permission_role_edit'),
                         url(r'admin/permission/role/create/$', 'admin_permission_role_edit', name = 'admin_permission_role_create'),
                         url(r'admin/permission/role/member/(?P<role_id>\d+)/list/$', 'admin_permission_role_member_list'),
                         url(r'admin/permission/role/member/(?P<role_id>\d+)/add/$', 'admin_permission_role_member_add'),
                         url(r'^accounts/register/$', 'register', name = 'sph_register'),
                         url(r'^accounts/register/(?P<emailHash>[a-zA-Z/\+0-9=]+)/$', 'register_hash', name = 'sph_register_hash'),
                         )
