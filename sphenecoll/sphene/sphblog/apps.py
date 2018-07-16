from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = u'sphene.sphblog'
    verbose_name = u"Blog"

    def ready(self):
        from sphene.community.sphutils import add_setting_defaults

        add_setting_defaults( {
            'blog_post_paging': 10,
        })
