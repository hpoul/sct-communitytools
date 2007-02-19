from django.contrib.sitemaps import Sitemap
from sphene.sphwiki.models import WikiSnip
from sphene.community.middleware import get_current_group

class WikiSnipSitemap(Sitemap):
    changefreq = 'hourly'
    priority = 1.0

    def items(self):
        group = get_current_group()
        return WikiSnip.objects.filter( group = group )

    def lastmod(self, obj):
        return obj.changed
