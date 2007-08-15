from django import template
from django import newforms as forms
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import signals
from django.dispatch import dispatcher
from django.newforms import widgets
from sphene.community.sphutils import get_sph_setting
from sphene.sphboard.models import Post, BoardUserProfile
from sphene.sphboard.views import PostForm
from sphene.contrib.libs.common.cache_inclusion_tag import cache_inclusion_tag

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

@register.inclusion_tag('sphene/sphboard/_displayCategories.html')
def sphboard_displayCategories( categories, maxDepth = 5, level = -1 ):
    if maxDepth < level:
        return { }
    return {'categories': categories,
            'level'     : level + 1,
            'maxDepth'  : maxDepth}

@register.inclusion_tag('sphene/sphboard/_displayLatestPost.html')
def sphboard_latestPost( latestPost, showSubject = 1 ):
    return { 'latestPost' : latestPost, 'showSubject': showSubject }

def sphboard_displayBreadcrumbs( category = None, post = None, linkall = False ):
    if category == None:
        if post == None: return { }
        category = post.category
        current = post
    else:
        current = category
    breadcrumbs = []
    while category != None:
        breadcrumbs.insert(0, category)
        category = category.parent
    return { 'thread': post, 'categories': breadcrumbs, 'current': not linkall and current, 'linkall': linkall }

@register.inclusion_tag('sphene/sphboard/_displayBreadcrumbs.html')
def sphboard_displayBreadcrumbsForThread( post, linkall = False ):
    return sphboard_displayBreadcrumbs( post = post, linkall = linkall )

@register.inclusion_tag('sphene/sphboard/_displayBreadcrumbs.html')
def sphboard_displayBreadcrumbsForCategory( category, linkall = False ):
    return sphboard_displayBreadcrumbs( category = category, linkall = linkall )

@register.inclusion_tag('sphene/sphboard/_displayUserName.html')
def sphboard_displayUserName( user ):
    return { 'user': user }

@register.inclusion_tag('sphene/sphboard/_pagination.html')
def sphboard_pagination( pages, page ):
    has_next = page < pages
    has_prev = page > 1
    return { 'page_range': range( 1, pages+1 ),
             'page': page,
             'pages': pages,
             'has_next': has_next,
             'has_prev': has_prev,
             'next': page + 1,
             'prev': page - 1,
             }

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
    return True



def authorinfo_cachekey(user_id):
    return 'sphboard_authorinfo_%s' % user_id

@cache_inclusion_tag(register,
                     'sphene/sphboard/_post_authorinfo.html',
                     cache_key_func=authorinfo_cachekey,
                     cache_time = get_sph_setting( 'board_authorinfo_cache_timeout' ))
def sphboard_post_authorinfo(user_id):
    if user_id is None:
        user = None
    else:
        user = User.objects.get(pk = user_id)
    return { 'author': user, }


def clear_authorinfo_cache(instance):
    cache.delete( authorinfo_cachekey( instance.id ) )

dispatcher.connect(clear_authorinfo_cache,
                   sender = User,
                   signal = signals.post_save)
