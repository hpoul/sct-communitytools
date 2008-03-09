# blog models


from django.db import models

from sphene.community.models import tag_get_labels
from sphene.community.sphutils import sphpermalink as permalink
from sphene.community.middleware import get_current_request
from sphene.sphboard.models import Post

BLOG_POST_STATUS_CHOICES = (
    (1, 'Draft'),
    (2, 'Published'),
    (3, 'Hidden'),
    )

class BlogPostExtension(models.Model):
    """
    Extension to a forum post - but actually only applicable for
    threads not posts.
    """
    post = models.ForeignKey(Post, unique = True)
    # The status is basically just for usability .. 
    # It is just important that this info gets populated to the Posts 'is_hidden' attribute.
    status = models.IntegerField( choices = BLOG_POST_STATUS_CHOICES )
    slug = models.CharField( max_length = 250, unique = True, db_index = True)

    def get_tag_labels(self):
        return tag_get_labels(self.post)

    def get_absolute_url(self):
        post = self.post
        date = post.postdate
        return ('sphene.sphblog.views.show_thread', (), { 'groupName': post.category.group.name,
                                                          'year': date.year,
                                                          'month': date.month,
                                                          'day': date.day,
                                                          'slug': self.slug,
                                                          })
    get_absolute_url = permalink(get_absolute_url, get_current_request)

