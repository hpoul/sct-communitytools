# blog views

#from sphene.sphblog.categorytypes import doinit

#doinit()

from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.db.models import Q
from django.core.paginator import Paginator, InvalidPage, EmptyPage


from sphene.community.models import Tag, tag_get_models_by_tag
from sphene.community.middleware import get_current_urlconf
from sphene.community.sphutils import add_rss_feed
from sphene.sphboard.views import showThread as sphboard_show_thread
from sphene.sphboard.models import Category, ThreadInformation, Post, get_tags_for_categories
from sphene.sphblog.models import BlogPostExtension
from sphene.community.sphutils import get_sph_setting, sph_reverse

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

def get_blog_posts_queryset(group, categories, year=None, month=None):
    """
    Return a list of blog posts.
    If given, year and month should be integers.
    """
    threads = BlogPostExtension.objects.filter( post__thread__isnull = True,
                                   post__category__group__id = group.id,
                                   post__category__id__in = map(lambda x: x.id, categories) ).order_by( '-post__postdate' )

    return _year_month_filter(threads, year, month)

def get_posts_queryset(group, categories, year=None, month=None):
    """
    Return a list of blog posts.
    If given, year and month should be integers.
    """
    threads = Post.objects.filter( thread__isnull = True,
                                   category__group__id = group.id,
                                   category__id__in = map(lambda x: x.id, categories) ).order_by( '-postdate' )

    return _year_month_filter(threads, year, month)

def _year_month_filter(threads, year=None, month=None):
    """
    Filter a queryset containing a 'postdate' field by year/month.
    """
    if month is not None and not 1 <= month <= 12:
        return None

    if year is not None:
        threads = threads.filter(postdate__year = year)
        # nested since there has to be a year to filter by month
        if month is not None:
            threads = threads.filter(postdate__month = month)

    return threads

def get_paged_objects(objects, page):
    paginator = Paginator(objects, get_sph_setting('blog_post_paging'))
    try:
        page = int(page)
    except ValueError:
        page = 1

    try:
        paged_objects = paginator.page(page)
    except (EmptyPage, InvalidPage):
        paged_objects = paginator.page(paginator.num_pages)

    return paged_objects

def get_category_info(group, category_id = None, category_slug = None):
    categories = get_board_categories(group)
    category = None
    if category_id is not None:
        category_id = int(category_id)
        categories = [category for category in categories
                      if category.id == category_id]
        if categories:
            category = categories[0]

    if category_slug is not None:
        categories = [category for category in categories
                      if category.slug == category_slug]
        if categories:
            category = categories[0]

    if not categories:
        return None
    return (categories, category)


def blogindex_redirect(request, group, category_id = None, page = 1, year=None, month=None):
    category_info = get_category_info(category_id = category_id,
                                      group = group)
    if not category_info:
        return Http404
    category = category_info[1]
    return HttpResponsePermanentRedirect(category.get_absolute_url())


def blogindex(request, group, category_id = None, category_slug = None, page = 1, year=None, month=None):
    """
    shows a blog posts list. year and month parameters
    are used for archive functionality.
    """

    category_info = get_category_info(category_id = category_id,
                                      category_slug = category_slug,
                                      group = group)
    if not category_info:
        return render_to_response('sphene/sphblog/nocategory.html',
                                  {},
                                  context_instance = RequestContext(request))
    context_variables = {}
    if year:
        context_variables['archive_year'] = year
        year = int(year)

        if month:
            context_variables['archive_month'] = month
            month = int(month)

    threads = get_posts_queryset(group, category_info[0], year, month)

    paged_threads = get_paged_objects(threads, page)

    allowpostcategories = filter(Category.has_post_thread_permission, category_info[0])
    #blog_feed_url = reverse('sphblog-feeds', urlconf=get_current_urlconf(), args = ('latestposts',), kwargs = { 'groupName': group.name })
    blog_feed_url = sph_reverse('sphblog-feeds');#, kwargs = { 'url': 'latestposts' })
    add_rss_feed( blog_feed_url, 'Blog RSS Feed' )
    all_tags = get_tags_for_categories( category_info[0] )

    context_variables.update({'allowpostcategories': allowpostcategories,
                              'threads': paged_threads,
                              'blog_feed_url': blog_feed_url,
                              'all_tags': all_tags,
                              'category': category_info[1],
                              'categories': category_info[0],
                              'group': group,
                              })

    return render_to_response( 'sphene/sphblog/blogindex.html',
                               context_variables,
                               context_instance = RequestContext(request) )

def show_tag_posts(request, group, tag_name, page = 1):
    categories = get_board_categories(group)

    if not page:
        page = 1

    if not categories:
        return render_to_response( 'sphene/sphblog/nocategory.html',{},
                                   context_instance = RequestContext(request) )

    tag = get_object_or_404(Tag, group = group,
                            name__exact = tag_name )
    threads = get_posts_queryset(group, categories)
    threads = tag_get_models_by_tag( threads, tag )
    paged_threads = get_paged_objects(threads, page)

    return render_to_response( 'sphene/sphblog/blogindex.html',
                               { 'threads': paged_threads,
                                 'tag': tag,
                                 'group': group,
                                 'categories': categories,
                                 },
                               context_instance = RequestContext(request) )


def postthread(request, group):
    category_id = request.POST['category']
    category = Category.objects.get( pk = category_id )

    return HttpResponseRedirect( category.get_absolute_post_thread_url() )

def show_thread_redirect(request, group, slug, category_slug = None, year = None, month = None, day = None):
    try:
        blogpost = BlogPostExtension.objects.get( slug__exact = slug)
    except BlogPostExtension.DoesNotExist:
        raise Http404
    return HttpResponsePermanentRedirect(blogpost.get_absolute_url())

def show_thread(request, group, slug, category_slug = None, year = None, month = None, day = None):
    try:
        blogpost = BlogPostExtension.objects.get( slug__exact = slug )
    except BlogPostExtension.DoesNotExist:
        raise Http404
    return sphboard_show_thread( request, blogpost.post.id, group )

