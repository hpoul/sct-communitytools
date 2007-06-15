

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.syndication.feeds import Feed
from sphene.sphboard.models import Category, Post


class LatestThreads(Feed):
    title_template = "sphene/sphboard/feeds/latestpost_title.html"
    description_template = "sphene/sphboard/feeds/latestpost_description.html"

    def get_object(self, bits):
        if len(bits) < 1:
            raise ObjectDoesNotExist
        return Category.objects.get( pk = bits[0] )

    def title(self, obj):
        return "Latest threads in %s" % obj.name

    def description(self, obj):
        return "Latest threads in %s" % obj.name

    def link(self, obj):
        return obj.get_absolute_url()

    def items(self, obj):
        return Post.objects.filter( category = obj,
                                    thread__isnull = True,
                                    ).order_by( '-postdate' )[:10]
    
