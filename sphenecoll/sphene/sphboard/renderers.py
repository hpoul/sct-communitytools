"""Renderer Classes for Sphene.
"""

from django.conf import settings
from django.core import exceptions
from django.utils.translation import ugettext as _, ugettext_lazy

from sphene.community.sphutils import get_sph_setting, get_method_by_name
from sphene.community.templatetags.sph_extras import sph_markdown
from sphene.contrib.libs.common.text import bbcode

class BaseRenderer(object):
    """ base class for all board renderers.
    see documentation on http://sct.sphene.net for more details. """
    
    label = 'Invalid'
    
    reference = 'Invalid'
    
    def __init__(self):
        pass
    
    def render(self, text):
        return text
        

class BBCodeRenderer(BaseRenderer):

    label = 'BBCode'

    reference ='<a href="http://en.wikipedia.org/wiki/BBCode" target="_blank">BBCode</a>'

    def bbcode_replace(test):
        print "bbcode ... %s %s %s" % (test.group(1), test.group(2), test.group(3))
        return test.group()

    def render(self, text):
         if get_sph_setting( 'board_auto_wiki_link_enabled', True ):
             from sphene.sphwiki import wikilink_utils
             return wikilink_utils.render_wikilinks(bbcode.bb2xhtml(text))
         else:
             return bbcode.bb2xhtml(text)

HTML_ALLOWED_TAGS = {
    'p': ( 'align' ),
    'em': (),
    'strike': (),
    'strong': (),
    'img': ( 'src', 'width', 'height', 'border', 'alt', 'title' ),
    'u': ( ),
}


class HtmlRenderer(BaseRenderer):
    
    label = 'HTML'
    
    reference = 'HTML (%s and %s)' % (", ".join(["'%s', " % tag for tag in HTML_ALLOWED_TAGS.keys()[:-1]]), HTML_ALLOWED_TAGS.keys()[-1])
    
    def htmlentities_replace(test):
        print "entity allowed: %s" % test.group(1)
        return test.group()

    def htmltag_replace(self, test):
        if HtmlRenderer.ALLOWED_TAGS.has_key( test.group(2) ):
            print "tag is allowed.... %s - %s" % (test.group(), test.group(3))
            if test.group(3) == None: return test.group()
            attrs = test.group(3).split(' ')
            allowedParams = ALLOWED_TAGS[test.group(2)]
            i = 1
            allowed = True
            for attr in attrs:
                if attr == '': continue
                val = attr.split('=')
                if not val[0] in allowedParams:
                    allowed = False
                    print "Not allowed: %s" % val[0]
                    break
            if allowed: return test.group()
        print "tag is not allowed ? %s" % test.group(2)
        return test.group().replace('<','&lt;').replace('>','&gt;')
        
    def render(self, text):
        """DISABLED.  Render the body as html"""
        if False:
            regex = re.compile("&(?!nbsp;)");
            body = regex.sub( "&amp;", text )
            regex = re.compile("<(/?)([a-zA-Z]+?)( .*?)?/?>")
            return regex.sub( htmltag_replace, body )
        return ""


class MarkdownRenderer(BaseRenderer):
    
    label = ugettext_lazy(u'Markdown')
    
    reference = '<a href="http://en.wikipedia.org/wiki/Markdown" target="_blank">%s</a>' % (ugettext_lazy(u'Markdown'))

    def render(self, text):
        return sph_markdown(text)

AVAILABLE_MARKUP = {
    'bbcode': BBCodeRenderer,
    'markdown': MarkdownRenderer,
    # 'html' : HtmlRenderer,
}

def _get_markup_choices(): 
    choices = []
    classes = {}

    enabled_markup = get_sph_setting( 'board_markup_enabled', ( 'bbcode', ) )
    custom_markup = get_sph_setting( 'board_custom_markup', {} )

    for en in enabled_markup:
        try:
            renderclass = AVAILABLE_MARKUP[en]
        except KeyError:
            try:
                renderer = custom_markup[en]
            except KeyError:
                raise exceptions.ImproperlyConfigured(
                    _(u"Custom renderer '%(renderer)s' needs a matching Render \
Class entry in your sphene settings 'board_custom_markup'")\
                     % {'renderer': en})
            renderclass = get_method_by_name(renderer)

        classes[en] = renderclass

        choices.append( ( en, renderclass.label ) )

    return tuple(choices), classes

POST_MARKUP_CHOICES, RENDER_CLASSES = _get_markup_choices()

def render_body(body, markup = None):
    """ Renders the given body string using the given markup.
    """
    if markup:
        try:
            renderer = RENDER_CLASSES[markup]()
            return renderer.render(body)
        except KeyError:
            raise exceptions.ImproperlyConfigured(
                _(u"Can't render markup '%(markup)s'") % {'markup':markup})
    else:
        return body

def describe_render_choices():
    choices = []
    for renderer, label in POST_MARKUP_CHOICES:
        choices.append(RENDER_CLASSES[renderer].reference)

    if len(choices) > 1:
        desc = u"%s or %s" % (", ".join(choices[:-1]), choices[-1])
    else:
        desc = choices[0]

    return ugettext_lazy('You can use %(description)s in your posts') % {'description':desc}
