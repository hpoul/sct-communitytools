import Image
import os
from time import time


from django import template
from django.template.context import RequestContext
from django.conf import settings
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from sphene.community.sphutils import HTML, get_sph_setting
from sphene.contrib.libs.markdown import mdx_macros
from sphene.contrib.libs.common.cache_inclusion_tag import cache_inclusion_tag
from sphene.community.models import CommunityUserProfile
from sphene.community.middleware import get_current_request, get_current_sphdata, get_current_group, get_current_user
from sphene.community.sphutils import add_rss_feed, sph_reverse


import logging
log = logging.getLogger('sphene.community.sph_extras')
    
register = template.Library()


class SimpleHelloWorldMacro (object):
    def handleMacroCall(self, doc, params):
        return doc.createTextNode("Hello World!")

import urllib2
from django.core.cache import cache

class IncludeMacro (mdx_macros.PreprocessorMacro):
    def handlePreprocessorMacroCall(self, params):
        if params.has_key( 'url' ):
            cache_key = settings.CACHE_MIDDLEWARE_KEY_PREFIX + 'sph_community_includemacro_' + params['url'] + '_' + params.get( 'start', '' ) + '_' + params.get( 'end', '' );
            cached_text = cache.get( cache_key )
            if cached_text:
                text = cached_text
            else:
                f = urllib2.urlopen( params['url'] )
                try:
                    start = params.get( 'start', None )
                    end = params.get( 'end', None )
                    if start or end:
                        text = ''
                        line = ''
                        if start:
                            for line in f:
                                if line.find( start ) == -1: pass
                                else: break
                        if end:
                            for line in f:
                                if line.find( end ) == -1:
                                    text += line
                                else: break
                                        
                    if not end:
                        text = f.read()

                    cache.set( cache_key, text, 3600 )
                finally:
                    f.close()
            return text
        #md = params['__md']
            #return sph_markdown( text, '', md )
        """
            ret = HTML( sph_markdown( text, '', md ) )
            sphdata = get_current_sphdata()
            if 'toc' in sphdata:
                ret.toc = sphdata['toc']
            return ret
        """
        return doc.createTextNode("Error, no 'url' given for include macro.")

class IncludeTemplateMacro (object):
    """
    allows users to include arbitrary html content through django's
    templating system.
    """
    def handleMacroCall(self, doc, params):
        if not params.has_key( 'templateName' ):
            return doc.createTextNode("Error, no 'templateName' given for includetemplate macro.")

        templateName = params['templateName']
        t = template.loader.get_template( templateName )
        c = template.Context( { 'params': params,
                                })

        return HTML( t.render(c) )


class NewsMacro (object):
    """
    displays threads in the given board category
    """
    def handleMacroCall(self, doc, params):
        from sphene.sphboard.models import Post

        if not params.has_key( 'category' ):
            return doc.createTextNode("Error, no 'category' or 'template' given for news macro.")

        limit = 'limit' in params and params['limit'] or 5
        templateName = 'sphene/sphboard/wikimacros/news.html'
        if params.has_key( 'template' ): templateName = params['template']
        
        category_ids = params['category'].split(',')
        threads = Post.objects.filter( category__id__in = category_ids, thread__isnull = True ).order_by( '-postdate' )[:limit]
        #threads = Post.objects.filter( category__id = params['category'], thread__isnull = True ).order_by( '-postdate' )[:limit]

        t = template.loader.get_template( templateName )
        baseURL = ''
        if params.has_key( 'baseURL' ): baseURL = params['baseURL']
        c = template.Context({ 'threads': threads,
                               'baseURL': baseURL,
                               'category': params['category'],
                               'params': params,
                               })
        
        return HTML( t.render(c) )


class NewsRSSLinkMacro (object):
    """
    displays threads in the given board category
    """
    def handleMacroCall(self, doc, params):
        from sphene.sphboard.models import Category

        category = params['category']
        try:
            categoryObj = Category.objects.get( pk = category, )
        except Category.DoesNotExist:
            return HTML( 'Category %s does not exist.' % category )

        url = categoryObj.get_absolute_url_rss_latest_threads()
        add_rss_feed( url, 'RSS Feed of latest threads' )
        return HTML( '<a href="%(url)s"><img src="%(media_url)ssphene/community/icons/feed-icon-14x14.png" border="0" alt="RSS Feed of latest threads" title="RSS Feed of latest threads" /></a>' % { 'url': url, 'media_url': settings.STATIC_URL } )


@register.filter
def sph_markdown(value, arg='', oldmd=None, extra_macros={}):
    try:
        from sphene.contrib.libs.markdown import markdown
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError, "Error in {% markdown %} filter: The Python markdown library isn't installed."
        return value
    else:
        safe_mode = arg == 'safe'
        macros = { 'helloWorld': SimpleHelloWorldMacro(),
                   'news': NewsMacro(),
                   'newsrss': NewsRSSLinkMacro(),
                   'include': IncludeMacro(),
                   'includetemplate': IncludeTemplateMacro(),
                   }
        macros.update(extra_macros),
        md = markdown.Markdown(value,
                               extensions = [ 'footnotes', 'wikilink', 'macros', 'toc' ],
                               extension_configs = { 'wikilink': [ ],
                                                     'macros': [ ( 'macros', macros
                                                                 )
                                                               ],
                                                     'toc': { 'include_header_one_in_toc': True, },
                                                     },
                               safe_mode = safe_mode,
                                 )
        md.number_headings = get_sph_setting('markdown_number_headings', True)
        md.top_heading_level = get_sph_setting('markdown_top_heading_level', 1)
        if oldmd and hasattr(oldmd,'header_numbers'): md.header_numbers = oldmd.header_numbers
        ret = md.toString()
        if hasattr(md, 'tocDiv'):
            sphdata = get_current_sphdata()
            sphdata['toc'] = mark_safe( md.tocDiv.toxml() )
        return ret

from sphene.community.sphutils import get_user_displayname, format_date

@register.filter
def sph_date(value, format = None):
    return format_date(value, format)

@register.filter
def sph_publicemailaddress(value):
    if get_sph_setting('community_email_anonymous_require_captcha'):
        # as a security constraint we don't return the public email
        # address if the user is not logged in.
        if not get_current_user().is_authenticated():
            validated = get_current_request().session.get('sph_email_captcha_validated', 0)

            # if the timeout is reached or the captcha was never entered
            # provide a link for the user to enter the captcha.
            if validated < time() - get_sph_setting('community_email_anonymous_require_captcha_timeout'):
                return mark_safe('<a href="%s">%s</a>' % (sph_reverse('sph_reveal_emailaddress', (), { 'user_id': value.id, }), _( 'Reveal this emailaddress')))

    if get_sph_setting('community_email_show_only_public'):
        try:
            return CommunityUserProfile.objects.get( user = value, ).public_emailaddress
        except CommunityUserProfile.DoesNotExist:
            pass
        return ''

    try:
        profile = CommunityUserProfile.objects.get( user = value, )
    except CommunityUserProfile.DoesNotExist:
        return "n/a" #value.email
    return profile.public_emailaddress or value.email

@register.filter
def sph_user_displayname(user):
    """ Returns the display name of the given user
    (No HTML, just text) """
    return get_user_displayname(user)

# This is for backwards compatibility
register.filter('sph_fullusername', sph_user_displayname)

@register.inclusion_tag('sphene/community/_display_username.html')
def sph_html_user(user):
    """ Returns the display name of a given user including a link to
    his profile. """
    return { 'user': user }

@register.filter
def sph_html_user(user):
    str = template.loader \
        .render_to_string( 'sphene/community/_display_username.html',
                           { 'user': user, },
                           context_instance = RequestContext(get_current_request()) )
    return str

@register.filter
def sph_iter(value):
    try:
        return value.__iter__()
    except AttributeError:
        return (value,).__iter__()


@register.filter
def sph_user_profile_link(value):
    """ Returns the URL to the user profile. """
    kwargs = { 'user_id': value.id, }
    return sph_reverse('sphene.community.views.profile', kwargs = kwargs )


import os

@register.filter
def sph_basename(value):
    basename = os.path.basename( value )
    return basename

@register.filter
def sph_dictget(value, param):
    return value.get(param, '')


from django.template import defaulttags, Node
from django.utils.encoding import smart_str

class SphURLNode(Node):
    " copied from django.template.defaulttags "
    def __init__(self, view_name, args, kwargs, asvar):
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        from django.core.urlresolvers import reverse, NoReverseMatch
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k,'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        
        url = ''
        try:
            url = sph_reverse(self.view_name,
                              args=args, kwargs=kwargs)
        except NoReverseMatch, e:
            if settings.SETTINGS_MODULE:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                try:
                    url = sph_reverse(project_name + '.' + self.view_name,
                                       args=args, kwargs=kwargs)
                except NoReverseMatch:
                    if self.asvar is None:
                        # Re-raise the original exception, not the one with
                        # the path relative to the project. This makes a
                        # better error message.
                        raise e
            else:
                if self.asvar is None:
                    raise e

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url

def sph_url2(*args, **kwargs):
    node = defaulttags.url(*args, **kwargs)
    return SphURLNode(node.view_name, node.args, node.kwargs, node.asvar)
sph_url2 = register.tag(sph_url2)


@register.simple_tag
def sph_url(view):
    req = get_current_request()
    urlconf = getattr(req, 'urlconf', None)
    try:
        return sph_reverse(view)
    except:
        log.exception('Unable to reverse sph_url for view %r' % view)
        return 'NOT FOUND'

@register.filter
def sph_minus(value, arg = 0):
    return value-arg

@register.filter
def sph_plus(value, arg = 0):
    return value+arg


@register.simple_tag
def sph_truncate(string, charlen, replacement):
    if len(string) > charlen:
        return escape(string[0:charlen-len(replacement)] + replacement)
    return escape(string)

@register.simple_tag
def sph_showavatar(user, maxwidth = None):
    profile = None
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        pass
    
    avatar = None
    avatar_width = None
    avatar_height = None

    get_avatar = get_sph_setting( 'community_user_get_avatar' )
    if get_avatar is not None:
        avatarinfo = get_avatar(user)
        print "asdf %s" % repr(avatarinfo)
        if avatarinfo is not None:
            avatar = avatarinfo['url']
            avatar_width = avatarinfo['width']
            avatar_height = avatarinfo['height']

    if avatar is None:
        if not profile or not profile.avatar:
            avatar = get_sph_setting( 'community_avatar_default' )
            log.error("got default avatar: %s", avatar)
            if not avatar:
                return ''
            avatar_width = get_sph_setting( 'community_avatar_default_width' )
            avatar_height = get_sph_setting( 'community_avatar_default_height' )
        else:
            avatar = profile.avatar.url
            avatar_width = profile.avatar_width
            avatar_height = profile.avatar_height
    
        if maxwidth is not None and maxwidth < avatar_width:
            avatar_height = round(float(avatar_height) * (float(maxwidth) / avatar_width))
            avatar_width = maxwidth
        
    log.info("avatar: %s", avatar)
    return '<img src="%s" width="%dpx" height="%dpx" alt="%s" class="sph_avatar"></img>' % (avatar, avatar_width, avatar_height, _(u'Users avatar'))

@register.inclusion_tag('sphene/community/templatetags/_form.html')
def sph_form(form, submit = ugettext_lazy(u'Submit') ):
    return { 'form': form,
             'submit': submit, }


@register.filter
def sph_thumbnail(file, size='200x200'):
    return resize(file, size)[0]

def resize(file, size='200x200'):
    # copied from http://www.djangosnippets.org/snippets/192/
    # defining the size
    width, height = size.split('x')
    # defining the filename and the miniature filename
    basename, format = file.name.rsplit('.', 1)
    miniature = basename + '_' + size + '.thumb.' +  format
    miniature_filename = os.path.join(settings.MEDIA_ROOT, miniature)
    miniature_url = os.path.join(settings.STATIC_URL, miniature)

    image = Image.open(file)

    # always calculate the width/height
    if width == 'X' or height == 'X':
        #filename = os.path.join(settings.MEDIA_ROOT, file)
        ox, oy = image.size
        
        if width != 'X':
            x = int(width)
            y = int(oy / (ox / float(x)))
        elif height != 'X':
            y = int(height)
            x = int(ox / (oy / float(y)))
        else:
            x = 200
            y = 200
    else:
        x = int(width)
        y = int(height)


    # if the image wasn't already resized, resize it
    if not os.path.exists(miniature_filename):
        image.thumbnail([x, y], Image.ANTIALIAS) # generate a 200x200 thumbnail
        image.save(miniature_filename, image.format)
    return (miniature_url, x, y)

@register.simple_tag
def get_orderby(orderby, key):
    plainkey = key
    if plainkey and plainkey[0]=='-':
        plainkey = plainkey[1:]

    if orderby==plainkey:
        return "-%s" % (plainkey)
    elif orderby[0]=='-' and orderby[1:]==plainkey:
        return plainkey
    return key
