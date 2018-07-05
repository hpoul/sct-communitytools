from django.conf import settings
from django.urls import include, re_path
from django.contrib.staticfiles import views
from django.views.generic import RedirectView
from django.contrib import admin
from django.contrib.auth import views as auth_views

defaultdict = {'groupName': 'example'}


urlpatterns = [
    # Example:
    # (r'^simpleproject/', include('simpleproject.foo.urls')),

    re_path('^$', RedirectView.as_view(url='/wiki/show/Start/', permanent=True)),

    re_path(r'^community/', include('sphene.community.urls'), defaultdict),
    re_path(r'^board/', include('sphene.sphboard.urls'), defaultdict),
    re_path(r'^wiki/', include('sphene.sphwiki.urls'), defaultdict),

    re_path(r'accounts/login/$', auth_views.LoginView.as_view()),
    re_path(r'accounts/logout/$', auth_views.LogoutView.as_view()),

    # Only for development
    re_path(r'^static/sphene/(.*)$',
            views.serve,
            {'document_root': settings.ROOT_PATH + '/../../static/sphene'}),

    # Uncomment this for admin:
    re_path(r'^admin/(.*)', admin.site.urls),
]
