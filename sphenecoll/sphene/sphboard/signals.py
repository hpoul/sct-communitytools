from django.core.cache import cache
from sphene.community.models import Group
import os


def clear_category_cache(sender, instance, created, *args, **kwargs):
    """ Clear cache for categories absolute url
    """
    if 'sph_init_data' in os.environ:
        return

    if isinstance(instance, Group):
        for category in instance.category_set.all():
            cache.delete(category._cache_key_absolute_url())
    else:
        cache.delete(instance._cache_key_absolute_url())


def clear_post_cache(sender, instance, *args, **kwargs):
    """ Clear absolute_urls of posts.
        If post being saved has changed 'thread' field or 'category' field or 'is_hidden' field then clear cache of all
        other posts in same thread as page numeration may be changed
    """
    if 'sph_init_data' in os.environ:
        return

    from sphene.community.models import Group
    from sphene.sphboard.models import Post, Category
    if instance.pk:  # this is not new object
        if isinstance(instance, Post):
            try:
                original = Post.objects.get(pk=instance.pk)
            except Post.DoesNotExist:
                return

            cache.delete(instance._cache_key_absolute_url())

            if instance.thread is None:
                thr = instance
            else:
                thr = instance.thread

            if thr and (original.thread != instance.thread
                        or original.is_hidden != instance.is_hidden
                        or original.category != instance.category):
                for post in thr.get_all_posts():
                    cache.delete(post._cache_key_absolute_url())
        elif isinstance(instance, Category):
            for post in instance.posts.all():
                cache.delete(post._cache_key_absolute_url())
        elif isinstance(instance, Group):
            for category in instance.category_set.all():
                for post in category.posts.all():
                    cache.delete(post._cache_key_absolute_url())

def clear_post_4_category_cache(sender, instance, *args, **kwargs):
    """ If post was created, was hidden or moved to another category then clear category cache
    """
    if not instance.pk:  #new post
        cache.delete(instance.category._cache_key_post_count())
        cache.delete(instance.category._cache_key_latest_post())
        if instance.thread is None:
            cache.delete(instance.category._cache_key_thread_count())
        else:
            cache.delete(instance.thread._cache_key_latest_post())
            cache.delete(instance._cache_key_post_count())
    else:
        from sphene.sphboard.models import Post
        try:
            old_post = Post.objects.get(pk=instance.pk)
            if old_post.category_id != instance.category_id or old_post.is_hidden != instance.is_hidden:
                cache.delete(old_post.category._cache_key_post_count())
                cache.delete(old_post.category._cache_key_latest_post())
                cache.delete(instance.category._cache_key_thread_count())
                cache.delete(instance._cache_key_post_count())
            elif old_post.thread != instance.thread:
                cache.delete(instance.category._cache_key_thread_count())
        except Post.DoesNotExist:
            pass


def mark_thread_moved_deleted(sender, instance, *args, **kwargs):
    """ If post was was hidden or moved to another category then mark it for post_save signal
    """
    if instance.pk:
        from sphene.sphboard.models import Post
        try:
            old_post = Post.objects.get(pk=instance.pk)
            if old_post.thread is None and \
               (old_post.category_id != instance.category_id or old_post.is_hidden != instance.is_hidden):
                setattr(instance, '_was_moved_deleted', True)
        except Post.DoesNotExist:
            pass

def clear_category_unread_after_post_move(sender, instance, *args, **kwargs):
    """ If post was was hidden or moved to another category then update unread status of all CategoryLastVisit
        objects - for all users
    """
    if instance.pk and getattr(instance, '_was_moved_deleted', False):
        category = instance.category
        for clv in category.categorylastvisit_set.all():
            category.update_unread_status(clv.user)

def clear_post_cache_on_delete(sender, instance, *args, **kwargs):
    """ Removed post might cause change in page numeration in thread
    """
    cache.delete(instance._cache_key_absolute_url())
    cache.delete(instance.category._cache_key_post_count())
    cache.delete(instance.category._cache_key_latest_post())
    cache.delete(instance.category._cache_key_thread_count())
    cache.delete(instance._cache_key_post_count())

    if instance.thread is None:
        thr = instance
    else:
        thr = instance.thread

    for post in thr.get_all_posts():
        cache.delete(post._cache_key_absolute_url())


def update_category_last_visit_cache(sender, instance, *args, **kwargs):
    last_visit_date = instance.oldlastvisit or instance.lastvisit
    cache.set(instance.category._cache_key_lastvisit_date(instance.user),
              last_visit_date)

# CACHE KEYS
# _cache_key_absolute_url - post absolute url
# _cache_key_absolute_url - category absolute url
# _cache_key_latest_post  - latest post for category
# _cache_key_thread_count - thread count for category
# _cache_key_post_count - number of posts in category
