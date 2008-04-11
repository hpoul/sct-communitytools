from django import template
from django import newforms as forms
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import signals
from django.dispatch import dispatcher
from django.newforms import widgets
from sphene.community.models import Group
from sphene.community.middleware import get_current_group, get_current_request
from sphene.community.sphutils import get_sph_setting
from sphene.community.models import CommunityUserProfile
from sphene.sphboard.models import Category, Post, BoardUserProfile, UserPostCount
from sphene.sphboard.views import PostForm, get_all_viewable_categories
from sphene.contrib.libs.common.cache_inclusion_tag import cache_inclusion_tag
from django.template.context import Context

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
    ret = {'categories': categories,
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
             'thread': thread, }


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
    return 'sphboard_authorinfo_%s_%s_%s' % \
        (str(group_id),str(user_id), language_code)

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

def clear_authorinfo_cache(instance):
    for group in Group.objects.all():
        clear_cache_all_languages(instance.id, group.id)

def clear_authorinfo_cache_postcount(instance):
    clear_cache_all_languages(instance.id, instance.group.id)

dispatcher.connect(clear_authorinfo_cache,
                   sender = User,
                   signal = signals.post_save)

dispatcher.connect(clear_authorinfo_cache_postcount,
                   sender = UserPostCount,
                   signal = signals.post_save)

def clear_posts_render_cache(instance):
    for group in Group.objects.all():
        allowed_categories = get_all_viewable_categories( group, instance.user )
        post_list = Post.objects.filter( category__id__in = allowed_categories,
                                         author = instance.user )
        for post in post_list:
            post.clear_render_cache()

dispatcher.connect(clear_posts_render_cache,
                   sender = CommunityUserProfile,
                   signal = signals.post_save)


class LatestThreadsNode(template.Node):
    def __init__(self, nodelist, categoryvar):
        self.nodelist = nodelist
        self.categoryvar = categoryvar

    def render(self, context):
        # TODO check permissions
        category_id = self.categoryvar.resolve(context)
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
    if len(bits) != 2:
        raise template.TemplateSyntaxError("%r requires a category as first argument." % bits[0])

    categoryvar = parser.compile_filter(bits[1])
    nodelist = parser.parse(('endsphboard_latest_threads',))
    parser.delete_first_token()
    return LatestThreadsNode(nodelist, categoryvar)



