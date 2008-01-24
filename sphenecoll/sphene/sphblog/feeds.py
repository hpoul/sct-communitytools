
from django.contrib.syndication.feeds import Feed

from sphene.community.middleware import get_current_group
from sphene.sphblog.models import BlogPostExtension
from sphene.sphblog.views import get_board_categories, get_posts_queryset
from sphene.sphboard.models import Post

class LatestBlogPosts(Feed):

    description = 'Latest Blog Posts'

    link = '/blog/'

    title_template = 'sphene/sphblog/feeds/latestposts_title.html'
    description_template = 'sphene/sphblog/feeds/latestposts_description.html'

    def title(self):
        group = get_current_group()
        return group.get_name()

    def items(self):
        group = get_current_group()
        categories = get_board_categories(group)
        threads = get_posts_queryset(group, categories )
        return threads


    def item_pubdate(self, obj):
        return obj.postdate

    def item_link(self, obj):
        try:
            return obj.blogpostextension_set.get().get_absolute_url()
        except BlogPostExtension.DoesNotExist:
            # This should never happen.
            return obj.get_absolute_url()

