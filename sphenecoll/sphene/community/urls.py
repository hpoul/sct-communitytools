from django.urls import re_path
from .views import accounts_forgot
from .views import accounts_login
from .views import accounts_logout
from .views import profile
from .views import profile_edit_mine
from .views import profile_edit
from .views import reveal_emailaddress
from .views import admin_permission_role_edit
from .views import admin_permission_role_groupmember_add
from .views import admin_permission_role_list
from .views import admin_permission_role_member_list
from .views import admin_permission_role_member_add
from .views import admin_permission_rolegroup_list
from .views import admin_permission_rolegroup_edit
from .views import admin_users
from .views import admin_user_switch_active
from .views import register
from .views import register_hash
from .views import email_change_hash
from .views import tags_json_autocompletion
from .views import captcha_image

urlpatterns = [
    re_path(r'captcha/(?P<token_id>\w+).jpg$', captcha_image),

    re_path(r'accounts/login/$', accounts_login),
    re_path(r'accounts/logout/$', accounts_logout),
    re_path(r'accounts/forgot/$', accounts_forgot),
    re_path(r'profile/(?P<user_id>\d+)/$', profile),
    re_path(r'profile/edit/$', profile_edit_mine),
    re_path(r'profile/edit/(?P<user_id>\d+)/$', profile_edit),
    re_path(r'profile/(?P<user_id>\d+)/reveal_address/$', reveal_emailaddress, name='sph_reveal_emailaddress'),

    re_path(r'admin/permission/role/list/$', admin_permission_role_list, name='community_admin_permission_role_list'),
    re_path(r'admin/permission/role/edit/(?P<role_id>\d+)/$', admin_permission_role_edit),
    re_path(r'admin/permission/role/create/$', admin_permission_role_edit, name='admin_permission_role_create'),
    re_path(r'admin/permission/role/member/(?P<role_id>\d+)/list/$', admin_permission_role_member_list),
    re_path(r'admin/permission/role/member/(?P<role_id>\d+)/add/$', admin_permission_role_member_add),
    re_path(r'admin/permission/role/member/(?P<role_id>\d+)/addgroup/$', admin_permission_role_groupmember_add),

    re_path(r'admin/permission/rolegroup/list/$', admin_permission_rolegroup_list,
            name='community_admin_permission_rolegroup_list'),
    re_path(r'admin/permission/rolegroup/edit/(?P<rolegroup_id>\d+)/$', admin_permission_rolegroup_edit),

    re_path(r'admin/users/$', admin_users, name='sph_admin_users'),
    re_path(r'admin/users/(?P<user_id>\d+)/switch/$', admin_user_switch_active, name='sph_admin_user_switch_active'),

    re_path(r'^accounts/register/$', register, name='sph_register'),
    re_path(r'^accounts/register/(?P<emailHash>[a-zA-Z\./\+0-9=]+)/(?P<email>[a-zA-Z%@\./\+0-9_-]+)/$', register_hash,
            name='sph_register_hash'),
    re_path(r'^accounts/email_change/(?P<email_change_hash>.+)/$', email_change_hash, name='sph_email_change_hash'),
    re_path(r'^tags/json/autocompletion/$', tags_json_autocompletion, name='sph_tags_json_autocompletion'),
]
