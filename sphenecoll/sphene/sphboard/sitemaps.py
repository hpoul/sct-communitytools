from django.contrib.sitemaps import Sitemap
from sphene.sphboard.models import Post
from sphene.community.middleware import get_current_group

class ThreadsSitemap(Sitemap):
    changefreq = 'hourly'
    priority = 0.5

    def items(self):
        group = get_current_group()
        return Post.objects.filter( category__group = group, thread__isnull = True, )

    def lastmod(self, obj):
        return obj.latestPost().postdate
