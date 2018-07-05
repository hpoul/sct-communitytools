from django.urls import re_path

from .views import config
from .views import addblock
from .views import edit_block_config
from .views import useasdefault
from .views import sortblocks
from .views import reverttodefault


urlpatterns = [
    re_path(r'^config/$', config, name='sphblockframework_config'),
    re_path(r'^addblock/$', addblock, name='sphblockframework_addblock'),
    re_path(r'^edit_block_config/(?P<block_config_id>\d+)/$', edit_block_config, ),
    re_path(r'^useasdefault/$', useasdefault, name='sphblockframework_useasdefault', ),
    re_path(r'^sortblocks/$', sortblocks, name='sphblockframework_sortblocks'),
    re_path(r'^sphblockframework_reverttodefault/$', reverttodefault, name='sphblockframework_reverttodefault', ),
]
