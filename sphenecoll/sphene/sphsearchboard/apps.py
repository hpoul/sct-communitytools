from django.apps import AppConfig


class SearchBoardConfig(AppConfig):
    name = u'sphene.sphsearchboard'
    verbose_name = u"SearchBoard"

    def ready(self):
        super().ready()
        # from djapian import load_indexes
        # load_indexes()
        print('sphsearchboard/apps.py -> ready')
        self.module.setup_indices()
