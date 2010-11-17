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
                         url(r'profile/(?P<user_id>\d+)/reveal_address/$', 'reveal_emailaddress', name = 'sph_reveal_emailaddress',),

                         url(r'admin/permission/role/list/$', 'admin_permission_role_list', name = 'community_admin_permission_role_list'),
                         url(r'admin/permission/role/edit/(?P<role_id>\d+)/$', 'admin_permission_role_edit'),
                         url(r'admin/permission/role/create/$', 'admin_permission_role_edit', name = 'admin_permission_role_create'),
                         url(r'admin/permission/role/member/(?P<role_id>\d+)/list/$', 'admin_permission_role_member_list'),
                         url(r'admin/permission/role/member/(?P<role_id>\d+)/add/$', 'admin_permission_role_member_add'),
                         url(r'admin/permission/role/member/(?P<role_id>\d+)/addgroup/$', 'admin_permission_role_groupmember_add', ),

                         url(r'admin/permission/rolegroup/list/$', 'admin_permission_rolegroup_list', name = 'community_admin_permission_rolegroup_list'),
                         url(r'admin/permission/rolegroup/edit/(?P<rolegroup_id>\d+)/$', 'admin_permission_rolegroup_edit',),

                         url(r'admin/users/$', 'admin_users', name='sph_admin_users'),
                         url(r'admin/users/(?P<user_id>\d+)/switch/$', 'admin_user_switch_active', name='sph_admin_user_switch_active'),

                         url(r'^accounts/register/$', 'register', name = 'sph_register'),
                         url(r'^accounts/register/(?P<emailHash>[a-zA-Z\./\+0-9=]+)/(?P<email>[a-zA-Z%@\./\+0-9_-]+)/$', 'register_hash', name = 'sph_register_hash'),
                         url(r'^tags/json/autocompletion/$', 'tags_json_autocompletion', name = 'sph_tags_json_autocompletion'),
                         )
