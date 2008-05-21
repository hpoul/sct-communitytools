from django.conf.urls.defaults import *



urlpatterns = patterns('',
                       (r'^$', 'django.views.generic.simple.redirect_to', {'url': 'show/Start/'}),
                                              )

snip = r'(?P<snipName>[\w/:\-.]+?)'

urlpatterns += patterns('sphene.sphwiki.views',
                        (r'^recentchanges/$', 'recentChanges'),
                        (r'^show/'          + snip + r'/$', 'showSnip'),
                        (r'^pdf/'           + snip + r'/$', 'generatePDF'),
                        (r'^edit/'          + snip + r'/$', 'editSnip'),
                        url(r'^editversion/'+ snip + r'/(?P<versionId>\d+)/$', 'editSnip', name = 'sphwiki_editversion'),
                        (r'^history/'       + snip + r'/$', 'history'),
                        (r'^diff/'          + snip + r'/(?P<changeId>\d+)/$', 'diff'),
                        (r'^attachments/edit/'   + snip + r'/(?P<attachmentId>\d+)/$', 'attachmentEdit'),
                        (r'^attachments/create/'   + snip + r'/$', 'attachmentCreate'),
                        (r'^attachments/list/'   + snip + r'/$', 'attachment'),

                        url(r'^tag/(?P<tag_name>\w+)/$', 'show_tag_snips', name = 'sphwiki_show_tag_snips'),
                        )
