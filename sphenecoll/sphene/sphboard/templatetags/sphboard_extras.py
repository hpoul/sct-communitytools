from django import template
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import signals, Q
from django.template.context import Context
from django.utils.safestring import mark_safe
from django.conf import settings

from sphene.contrib.libs.common.cache_inclusion_tag import cache_inclusion_tag

from sphene.community.models import Group
from sphene.community.middleware import get_current_group, get_current_request, get_current_user
from sphene.community.sphutils import get_sph_setting
from sphene.community.models import CommunityUserProfile
from sphene.community.permissionutils import has_permission_flag
from sphene.community import PermissionDenied

from sphene.sphboard.models import Category, Post, BoardUserProfile, UserPostCount, Monitor
from sphene.sphboard.views import PostForm, get_all_viewable_categories, enable_wysiwyg_editor

register = template.Library()

@register.filter
def sphrepeat(value, arg):
    ret = "";
    for x in range(arg):
        ret += value
    return ret

@register.filter
def sphminus(value, arg):
    return value-arg

@register.filter
def sphrange(value):
    return range( value )

@register.inclusion_tag('sphene/sphboard/_displayCategories.html', takes_context=True)
def sphboard_displayCategories(context, categories, maxDepth = 5, level = -1 ):
    if maxDepth < level:
        return { }
    ret = {'categories': [ c for c in categories \
                               if c.get_category_type().is_displayed() ],
           'level'     : level + 1,
           'maxDepth'  : maxDepth}
    retctx = Context(context)
    retctx.update(ret)
    return retctx

@register.inclusion_tag('sphene/sphboard/_displayLatestPost.html')
def sphboard_latestPost( latestPost, showSubject = 1 ):
    return { 'latestPost' : latestPost, 'showSubject': showSubject }

def sphboard_displayBreadcrumbs( category = None, post = None, linkall = False, show_board_link = True ):
    if category == None:
        if post == None: return { 'show_board_link': show_board_link, }
        category = post.category
        current = post
    else:
        current = category
    breadcrumbs = []
    while category != None:
        breadcrumbs.insert(0, category)
        category = category.parent
    return { 'thread': post, 'categories': breadcrumbs, 'current': not linkall and current, 'linkall': linkall, 'show_board_link': show_board_link }

@register.inclusion_tag('sphene/sphboard/_displayBreadcrumbs.html')
def sphboard_displayBreadcrumbsForThread( post, linkall = False, show_board_link = True ):
    return sphboard_displayBreadcrumbs( post = post, linkall = linkall, show_board_link = show_board_link )

@register.inclusion_tag('sphene/sphboard/_displayBreadcrumbs.html')
def sphboard_displayBreadcrumbsForCategory( category, linkall = False, show_board_link = True ):
    return sphboard_displayBreadcrumbs( category = category, linkall = linkall, show_board_link = show_board_link )

@register.inclusion_tag('sphene/sphboard/_displayUserName.html')
def sphboard_displayUserName( user ):
    return { 'user': user }

@register.inclusion_tag('sphene/sphboard/_displayPostForm.html')
def sphboard_quick_thread( category ):
    return quick_post(category)


@register.inclusion_tag('sphene/sphboard/_displayPostForm.html')
def sphboard_quick_reply( thread ):
    return quick_post(thread.category, thread)

def quick_post(category, thread = None):
    subject = u''
    if thread is not None:
        subject = u'Re: ' + thread.subject
        form_action = thread.get_absolute_postreplyurl()
    else:
        form_action = category.get_absolute_post_thread_url()

    MyPostForm = PostForm
    category_type = category.get_category_type()
    
    if category_type is not None:
        MyPostForm = category_type.get_post_form_class(thread, None)

    form = MyPostForm(initial={'subject': subject} )
    form.init_for_category_type(category_type, None)
    return { 
        'form': form,
        'form_action': form_action }

### sphboard_displayPostForm is deprecated, there is a view function for this !!
@register.inclusion_tag('sphene/sphboard/_displayPostForm.html', takes_context=True)
def sphboard_displayPostForm(context, post = None):
    #PostForm = forms.models.form_for_model(Post)
    if post != None:
        PostForm.base_fields['subject'].initial = 'Re: %s' % post.subject
    """
    body = PostForm.base_fields['body'].widget = TinyMCE( )
    body.mce_settings = { 'mode': 'exact',
                          'theme': 'advanced',
                          'plugins': 'emotions',
                          'theme_advanced_buttons3_add': 'emotions',
                          'theme_advanced_toolbar_location': 'top',
                          'theme_advanced_disable': 'styleselect,formatselect',
                          'theme_advanced_buttons1' : 'bold,italic,underline,strikethrough,separator,justifyleft,justifycenter,justifyright,justifyfull,separator,emotions',
                          'theme_advanced_buttons2' : '',
                          'theme_advanced_buttons3' : '',
                          }
    """
    body = PostForm.base_fields['body'].widget
    body.attrs['cols'] = 80
    body.attrs['rows'] = 10
    form = PostForm()
    if context.has_key('category'): category = context['category']
    else: category = None
    if context.has_key('thread'): thread = context['thread']
    else: thread = None

    return { 'form': form,
             'category': category,
             'thread': thread,
             'bbcodewysiwyg': enable_wysiwyg_editor(), }


@register.filter
def sphboard_default_notify_me(user):
    try:
        profile = BoardUserProfile.objects.get(user = user)
        if profile.default_notifyme_value is False:
            return False
    except BoardUserProfile.DoesNotExist:
        pass
    return get_sph_setting( 'board_default_notifyme' )



def authorinfo_cachekey(user_id, group_id = None, language_code = None):
    if group_id is None:
        group_id = get_current_group().id
    if language_code is None:
        language_code = getattr(get_current_request(), 'LANGUAGE_CODE', '')
    return '%s_sphboard_authorinfo_%s_%s_%s' % \
        (settings.CACHE_MIDDLEWARE_KEY_PREFIX, str(group_id),str(user_id), language_code)

@cache_inclusion_tag(register,
                     'sphene/sphboard/_post_authorinfo.html',
                     cache_key_func=authorinfo_cachekey,
                     cache_time = get_sph_setting( 'board_authorinfo_cache_timeout' ))
def sphboard_post_authorinfo(user_id):
    if user_id is None:
        user = None
    else:
        user = User.objects.get(pk = user_id)

    return { 'author': user,
             'post_count': UserPostCount.objects.get_post_count(user, get_current_group()) }


def clear_cache_all_languages(user_id, group_id):
    from django.conf import settings
    if not hasattr(settings, 'LANGUAGES'):
        return
    for code, name in settings.LANGUAGES:
        cache.delete( authorinfo_cachekey( user_id, group_id, code ) )

def clear_authorinfo_cache(instance, **kwargs):
    for group in Group.objects.all():
        clear_cache_all_languages(instance.id, group.id)

def clear_authorinfo_cache_postcount(instance, **kwargs):
    clear_cache_all_languages(instance.user.id, instance.group.id)

signals.post_save.connect(clear_authorinfo_cache,
                   sender = User)

signals.post_save.connect(clear_authorinfo_cache_postcount,
                   sender = UserPostCount)

def clear_posts_render_cache(instance, **kwargs):
    for group in Group.objects.all():
        allowed_categories = get_all_viewable_categories( group, instance.user )
        post_list = Post.objects.filter( category__id__in = allowed_categories,
                                         author = instance.user )
        for post in post_list:
            post.clear_render_cache()

signals.post_save.connect(clear_posts_render_cache,
                   sender = CommunityUserProfile)


class LatestThreadsNode(template.Node):
    def __init__(self, nodelist, categoryvar):
        self.nodelist = nodelist
        self.categoryvar = categoryvar

    def render(self, context):
        # TODO check permissions
        category_id = None
        if self.categoryvar:
            category_id = self.categoryvar.resolve(context)
        if not category_id:
            # if no category id is given simply display all categories
            # of the current group.
            category = None
            categories = get_all_viewable_categories(get_current_group(), get_current_user())
            threads = Post.objects.filter(category__id__in = categories,
                                          thread__isnull = True,).order_by('-postdate')
        else:
            category = Category.objects.get( pk = category_id )
            threads = Post.objects.filter(category = category,
                                          thread__isnull = True,).order_by('-postdate')
        context.push()
        context['threads'] = threads
        context['category'] = category
        output = self.nodelist.render(context)
        context.pop()
        return output



@register.tag(name='sphboard_latest_threads')
def sphboard_latest_threads(parser, token):
    bits = list(token.split_contents())
    #if len(bits) != 2:
    #    raise template.TemplateSyntaxError("%r requires a category as first argument." % bits[0])

    if len(bits) == 2:
        categoryvar = parser.compile_filter(bits[1])
    else:
        categoryvar = None
    nodelist = parser.parse(('endsphboard_latest_threads',))
    parser.delete_first_token()
    return LatestThreadsNode(nodelist, categoryvar)


class RecursiveCategoryIteratorNode(template.Node):
    def __init__(self, nodelist, categorytypevar):
        self.nodelist = nodelist
        self.categorytypevar = categorytypevar

    def recursive_render(self, context, parent, depth = 0):
        filter = Category.objects.filter(
            group = get_current_group(),)

        if self.categorytypevar is not None:
            categorytype = self.categorytypevar.resolve(context)

            filter = filter.filter(category_type__in = categorytype.split(','))
            #(TaskCategoryType.name, DivisionCategoryType.name),)
        if parent is None:
            filter = filter.filter(parent__isnull = True)
        else:
            filter = filter.filter(parent = parent)

        output = []

        for category in filter:
            if not category.has_view_permission():
                continue
            # render children first
            children = self.recursive_render(context, category, depth + 1)

            # render the current category
            context.push()
            context['category'] = category
            context['children'] = mark_safe(children)
            context['depth'] = depth
            context['depthrange'] = xrange(depth)
            output.append(self.nodelist.render(context))
            context.pop()

        return ''.join(output)

    def render(self, context):
        return self.recursive_render(context, None)

@register.tag(name = 'sphboard_recursive_category_iterator')
def sphboard_recursive_category_iterator(parser, token):
    bits = list(token.split_contents())
    if len(bits) > 2:
        raise template.TemplateSyntaxError("%r requires at most one argument." % bits[0])

    categorytypevar = None
    if len(bits) > 1:
        categorytypevar = parser.compile_filter(bits[1])


    nodelist = parser.parse(('endsphboard_recursive_category_iterator',))
    parser.delete_first_token()
    return RecursiveCategoryIteratorNode(nodelist, categorytypevar)


@register.inclusion_tag('sphene/sphboard/_displayThreadSummary.html', takes_context=True)
def sphboard_displayThreadSummary(context, thread):
    """
        Display last 10 posts in thread
    """
    posts = thread.get_all_posts().order_by('-postdate')[:11]
    return { 'posts': posts,
             'thread': thread}

@register.simple_tag
def user_posts_count(user):
    return UserPostCount.objects.get_post_count(user, get_current_group())

def show_active_monitors(context, profile_user):
    user = context['user']
    request = context['request']

    if user==profile_user:
        monitors = Monitor.objects.filter(Q(thread=None)|Q(thread__is_hidden=0),
                                          user = profile_user,
                                          group = get_current_group()
                                          )
    else:
        if not has_permission_flag(request.user, 'community_manage_users'):
            raise PermissionDenied()
        monitors = Monitor.objects.filter(Q(thread=None)|Q(thread__is_hidden=0),
                                          user = profile_user,
                                          group = get_current_group()
                                          )
    return {'monitors':monitors,
            'request':request,
            'is_current_user':user==profile_user}
register.inclusion_tag('sphene/sphboard/templatetags/_show_active_monitors.html', takes_context=True)(show_active_monitors)
