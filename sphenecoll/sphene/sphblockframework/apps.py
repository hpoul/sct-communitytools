from django.apps import AppConfig
from django.conf import settings


class BlockFrameworkConfig(AppConfig):
    name = u'sphene.sphblockframework'
    verbose_name = u"Block Framework"

    def ready(self):
        from sphene.community.sphutils import get_sph_setting
        from sphene.community import sphsettings
        jsincludes = get_sph_setting( 'community_jsincludes', [])
        # jquery is already added by the community application.
        #jsincludes.append(settings.STATIC_URL + 'sphene/community/jquery-1.2.3.min.js')
        jsincludes.append(settings.STATIC_URL + 'sphene/community/jquery.dimensions.js')
        jsincludes.append(settings.STATIC_URL + 'sphene/community/ui.mouse.js')
        #jsincludes.append(settings.STATIC_URL + 'sphene/community/ui.draggable.js')
        jsincludes.append(settings.STATIC_URL + 'sphene/community/ui.droppable.js')
        jsincludes.append(settings.STATIC_URL + 'sphene/community/ui.sortable.js')
        jsincludes.append(settings.STATIC_URL + 'sphene/sphblockframework/blocksorting.js')

        sphsettings.set_sph_setting( 'community_jsincludes', jsincludes )
