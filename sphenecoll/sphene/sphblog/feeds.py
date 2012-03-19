

from django.http import Http404
from django.contrib.syndication.views import Feed

from sphene.community.middleware import get_current_group
from sphene.sphblog.models import BlogPostExtension
from sphene.sphblog.views import get_board_categories, get_blog_posts_queryset
from sphene.sphboard.models import Post

class LatestBlogPosts(Feed):

    description = 'Latest Blog Posts'

    link = '/blog/'

    title_template = 'sphene/sphblog/feeds/latestposts_title.html'
    description_template = 'sphene/sphblog/feeds/latestposts_description.html'

    def get_object(self, request, category_id = None):
        group = get_current_group()
        categories = get_board_categories(group)
        if not category_id:
            return categories
        #category_id = int(bits[0])
        categories = [category for category in categories \
                          if category.id == category_id]
        if not categories:
            raise Http404
        return categories

    def title(self, obj):
        if len(obj) == 1:
            return obj[0].name
        group = get_current_group()
        return group.get_name()

    def items(self, obj):
        group = get_current_group()
        categories = obj
        threads = get_blog_posts_queryset(group, categories )
        return threads

    def item_pubdate(self, item):
        return item.post.postdate

    def item_link(self, item):
        return item.get_absolute_url()

    def item_categories(self, item):
        return item.get_tag_labels()

