from django.conf.urls.defaults import *



urlpatterns = patterns('sphene.sphblockframework.views',
                       url(r'^config/$', 'config', name = 'sphblockframework_config'),
                       url(r'^addblock/$', 'addblock', name = 'sphblockframework_addblock'),
                       url(r'^edit_block_config/(?P<block_config_id>\d+)/$', 'edit_block_config', ),
                       url(r'^useasdefault/$', 'useasdefault', name = 'sphblockframework_useasdefault', ),
                       url(r'^sortblocks/$', 'sortblocks', name= 'sphblockframework_sortblocks' ),
                       url(r'^sphblockframework_reverttodefault/$', 'reverttodefault', name = 'sphblockframework_reverttodefault', ),
                       )


