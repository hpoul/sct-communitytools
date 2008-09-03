# blog views

#from sphene.sphblog.categorytypes import doinit

#doinit()

from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.db.models import Q

from sphene.community.models import Tag, tag_get_models_by_tag
from sphene.community.middleware import get_current_urlconf
from sphene.community.sphutils import add_rss_feed
from sphene.sphboard.views import showThread as sphboard_show_thread
from sphene.sphboard.models import Category, ThreadInformation, Post, get_tags_for_categories
from sphene.sphblog.models import BlogPostExtension

def get_board_categories(group):
    """
    Returns a list of all categories of type 'sphblog'
    """
    # First fetch all categories matching the group and type.
    categories = Category.objects.filter(
        Q( group = group ) &
        Q( category_type = 'sphblog' ) | Q( category_type = 'sphbloghidden'))
    # Now check permissions
    blogcategories = filter(Category.has_view_permission, categories)
    return blogcategories

def get_posts_queryset(group, categories):
    threads = Post.objects.filter( thread__isnull = True,
                                   category__group__id = group.id,
                                   category__id__in = map(lambda x: x.id, categories) ).order_by( '-postdate' )
    return threads

def blogindex(request, group, category_id = None):
    categories = get_board_categories(group)
    if category_id is not None:
        category_id = int(category_id)
        categories = [category for category in categories \
                          if category.id == category_id]
    if not categories:
        return render_to_response( 'sphene/sphblog/nocategory.html',
                                   { },
                                   context_instance = RequestContext(request) )

    threads = get_posts_queryset(group, categories)

    allowpostcategories = filter(Category.has_post_thread_permission, categories)
    #blog_feed_url = reverse('sphblog-feeds', urlconf=get_current_urlconf(), args = ('latestposts',), kwargs = { 'groupName': group.name })
    blog_feed_url = reverse('sphblog-feeds', urlconf=get_current_urlconf(), kwargs = { 'url': 'latestposts' })
    add_rss_feed( blog_feed_url, 'Blog RSS Feed' )
    all_tags = get_tags_for_categories( categories )
    return render_to_response( 'sphene/sphblog/blogindex.html',
                               { 'allowpostcategories': allowpostcategories,
                                 'threads': threads,
                                 'blog_feed_url': blog_feed_url,
                                 'all_tags': all_tags,
                                 },
                               context_instance = RequestContext(request) )

def show_tag_posts(request, group, tag_name):
    categories = get_board_categories(group)

    if not categories:
        return render_to_response( 'sphene/sphblog/nocategory.html',{},
                                   context_instance = RequestContext(request) )

    tag = get_object_or_404(Tag, group = group,
                            name__exact = tag_name )
    threads = get_posts_queryset(group, categories)
    threads = tag_get_models_by_tag( threads, tag )

    return render_to_response( 'sphene/sphblog/blogindex.html',
                               { 'threads': threads,
                                 'tag': tag,
                                 },
                               context_instance = RequestContext(request) )


def postthread(request, group):
    category_id = request.POST['category']
    category = Category.objects.get( pk = category_id )

    return HttpResponseRedirect( category.get_absolute_post_thread_url() )


def show_thread(request, group, slug, year = None, month = None, day = None):
    try:
        blogpost = BlogPostExtension.objects.get( slug__exact = slug )
    except BlogPostExtension.DoesNotExist:
        raise Http404
    return sphboard_show_thread( request, blogpost.post.id, group )


