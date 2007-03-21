from django.conf.urls.defaults import *



urlpatterns = patterns('',
                       (r'^$', 'django.views.generic.simple.redirect_to', {'url': 'show/Start'}),
                                              )

snip = r'(?P<snipName>[\w/:\-]+?)'

urlpatterns += patterns('sphene.sphwiki.views',
                        (r'^recentchanges/$', 'recentChanges'),
                        (r'^show/'          + snip + r'/$', 'showSnip'),
                        (r'^edit/'          + snip + r'/$', 'editSnip'),
                        (r'^history/'       + snip + r'/$', 'history'),
                        (r'^diff/'          + snip + r'/(?P<changeId>\d+)/$', 'diff'),
                        (r'^attachments/'   + snip + r'/create/$', 'attachmentEdit'),
                        (r'^attachments/'   + snip + r'/(?P<attachmentId>\d+)/$', 'attachmentEdit'),
                        (r'^attachments/'   + snip + r'/$', 'attachment'),
                        )
