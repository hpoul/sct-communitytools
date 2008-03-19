from django.contrib.sitemaps import Sitemap
from sphene.sphboard.models import Post, Category
from sphene.community.middleware import get_current_group

class ThreadsSitemap(Sitemap):
    changefreq = 'hourly'
    priority = 0.5

    def items(self):
        group = get_current_group()

        ## Check permissions
        all_categories = Category.objects.filter( group = group )
        allowed_categories = ()
        for category in all_categories:
            if category.has_view_permission( ):
                allowed_categories += (category.id,)

        return Post.objects.filter( category__id__in = allowed_categories, thread__isnull = True, )

    def lastmod(self, obj):
        return obj.get_latest_post().postdate

    def location(self, obj):
        return obj.get_threadinformation().get_absolute_url_nopaging()
