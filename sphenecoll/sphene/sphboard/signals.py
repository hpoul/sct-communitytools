from django.core.cache import cache
from django.conf import settings

from sphene.community.sphutils import get_sph_setting

def clear_category_cache(sender, instance, created, *args, **kwargs):
    """ Clear cache for categories absolute url
    """
    if isinstance(instance, Group):
        for category in instance.category_set.all():
            key = '%s_cat_abs_url_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, category.pk)
            cache.delete(key)
    else:
        key = '%s_cat_abs_url_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, instance.pk)
        cache.delete(key)


def clear_post_cache(sender, instance, *args, **kwargs):
    """ If post being saved has changed 'thread' field or 'category' field or 'is_hidden' field then clear cache of all
        other posts in same thread as page numeration may be changed
    """
    from sphene.community.models import Group
    from sphene.sphboard.models import Post, Category
    key = '%s_post_abs_url_%%s_%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX,
                                         get_sph_setting('board_slugify_links'),
                                         get_sph_setting( 'board_post_paging' ))
    if instance.pk:  # this is not new object
        if isinstance(instance, Post):
            try:
                original = Post.objects.get(pk=instance.pk)
            except Post.DoesNotExist:
                return

            cache.delete(key % (instance.pk))

            if instance.thread is None:
                thr = instance
            else:
                thr = instance.thread

            if thr and (original.thread.pk != instance.thread.pk
                        or original.is_hidden != instance.is_hidden
                        or original.category != instance.category):
                for post in thr.get_all_posts():
                    cache.delete(key % (post.pk))
        elif isinstance(instance, Category):
            for post in instance.posts.all():
                cache.delete(key % (post.pk))
        elif isinstance(instance, Group):
            for category in instance.category_set.all():
                for post in category.posts.all():
                    cache.delete(key % (post.pk))

def clear_post_cache_on_delete(sender, instance, *args, **kwargs):
    """ Removed post might cause change in page numeration in thread
    """
    key = '%s_post_abs_url_%%s_%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX,
                                         get_sph_setting('board_slugify_links'),
                                         get_sph_setting( 'board_post_paging' ))
    cache.delete(key % (instance.pk))

    if instance.thread is None:
        thr = instance
    else:
        thr = instance.thread

    for post in thr.get_all_posts():
        cache.delete(key % (post.pk))


