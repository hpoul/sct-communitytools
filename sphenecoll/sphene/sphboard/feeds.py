from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.contrib.syndication.views import Feed
from django.utils.translation import ugettext as _

from sphene.sphboard.models import Category, Post
from sphene.community.models import Group


class LatestThreads(Feed):
    def get_object(self, request, category_id, group=None):
        category = Category.objects.get( pk = category_id )
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

    def item_title(self, item):
        return item.subject

    def item_description(self, item):
        return item.body_escaped(with_signature=False)

    def item_pubdate(self, item):
        return item.postdate


class LatestGlobalThreads(Feed):
    def get_object(self, request, group=None):
        return group

    def title(self, obj):
        return _(u'Latest threads at %(obj_name)s') % {'obj_name':obj.longname and obj.longname or obj.name}

    def description(self, obj):
        return _(u'Latest threads at %(obj_name)s') % {'obj_name':obj.longname and obj.longname or obj.name}

    def link(self, obj):
        if obj is None:
            return '/'
        return obj.get_baseurl()

    def items(self, obj):
        return Post.objects.filter( category__group=obj,
                                    thread__isnull = True,
                                    ).order_by( '-postdate' )[:10]

    def item_title(self, item):
        return item.subject

    def item_description(self, item):
        return item.body_escaped(with_signature=False)

    def item_pubdate(self, item):
        return item.postdate
