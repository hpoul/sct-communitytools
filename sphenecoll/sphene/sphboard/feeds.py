from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.syndication.feeds import Feed
from django.utils.translation import ugettext as _

from sphene.sphboard.models import Category, Post


class LatestThreads(Feed):
    title_template = "sphene/sphboard/feeds/latestpost_title.html"
    description_template = "sphene/sphboard/feeds/latestpost_description.html"

    def get_object(self, bits):
        if len(bits) < 1 or bits[0] == '':
            raise ObjectDoesNotExist
        
        category = Category.objects.get( pk = bits[0] )
        if not category.has_view_permission():
            raise PermissionDenied
        return category

    def title(self, obj):
        return _(u'Latest threads in %(obj_name)s') % {'obj_name':obj.name}

    def description(self, obj):
        return _(u'Latest threads in %(obj_name)s') % {'obj_name':obj.name}

    def link(self, obj):
        if obj is None:
            return '/'
        return obj.get_absolute_url()

    def items(self, obj):
        return Post.objects.filter( category = obj,
                                    thread__isnull = True,
                                    ).order_by( '-postdate' )[:10]

    def item_pubdate(self, item):
        return item.postdate

