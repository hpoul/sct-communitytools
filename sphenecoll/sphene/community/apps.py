from django.apps import AppConfig


class CommunityConfig(AppConfig):
    name = u'sphene.community'
    verbose_name = u"Community"

    def ready(self):
        import sphene.community.signals.handlers
