from django.conf.urls.defaults import *

from django.conf.urls.defaults import *



urlpatterns = patterns('',
                       (r'^$', 'django.views.generic.simple.redirect_to', {'url': 'show/Start'}),
                                              )
urlpatterns += patterns('sphene.sphwiki.views',
                        (r'^show/(?P<snipName>[\w/]+)/$', 'showSnip'),
                        (r'^edit/(?P<snipName>[\w/]+)/$', 'editSnip'),
                        (r'^attachments/(?P<snipName>[\w/]+?)/create/$', 'attachmentEdit'),
                        (r'^attachments/(?P<snipName>[\w/]+)/(?P<attachmentId>\d+)/$', 'attachmentEdit'),
                        (r'^attachments/(?P<snipName>[\w/]+)/$', 'attachment'),
                        )
