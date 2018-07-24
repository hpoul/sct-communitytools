from django.urls import re_path
from django.views.generic import RedirectView

from .views import recentChanges
from .views import showSnip
from .views import generatePDF
from .views import history
from .views import editSnip
from .views import diff
from .views import attachmentEdit
from .views import attachment
from .views import attachmentCreate
from .views import show_tag_snips


urlpatterns = [
    re_path(r'^$', RedirectView.as_view(url='show/Start/'))
]

snip = r'(?P<snipName>[\w/:\-.]+?)'

urlpatterns += [
    re_path(r'^recentchanges/$', recentChanges, name='sphwiki-recentchanges'),
    re_path(r'^show/' + snip + r'/$', showSnip, name='sphwiki-show'),
    re_path(r'^pdf/' + snip + r'/$', generatePDF, name='sphwiki-pdf'),
    re_path(r'^edit/' + snip + r'/$', editSnip, name='sphwiki-edit'),
    re_path(r'^editversion/' + snip + r'/(?P<versionId>\d+)/$', editSnip, name='sphwiki_editversion'),
    re_path(r'^history/' + snip + r'/$', history, name='sphwiki-history'),
    re_path(r'^diff/' + snip + r'/(?P<changeId>\d+)/$', diff),
    re_path(r'^attachments/edit/' + snip + r'/(?P<attachmentId>\d+)/$', attachmentEdit, name='sphwiki-attachments-edit'),
    re_path(r'^attachments/create/' + snip + r'/$', attachmentCreate, name='sphwiki-attachments-create'),
    re_path(r'^attachments/list/' + snip + r'/$', attachment, name='sphwiki-attachments-list'),

    re_path(r'^tag/(?P<tag_name>\w+)/$', show_tag_snips, name='sphwiki_show_tag_snips'),
]
