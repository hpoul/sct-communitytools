"""Renderer Classes for Sphene.
"""
import re

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

    def render(self, text, apply_spammer_limits=False):
        return text


class BBCodeRenderer(BaseRenderer):
    label = 'BBCode'

    reference = '<a href="http://en.wikipedia.org/wiki/BBCode" target="_blank">BBCode</a>'

    def bbcode_replace(test):
        return test.group()

    def render(self, text, apply_spammer_limits=False):
        if get_sph_setting('board_auto_wiki_link_enabled', True):
            from sphene.sphwiki import wikilink_utils
            return wikilink_utils.render_wikilinks(bbcode.bb2xhtml(text))
        else:
            return bbcode.bb2xhtml(text, apply_spammer_limits=apply_spammer_limits)


HTML_ALLOWED_TAGS = {
    'p': ('align', ),
    'em': (),
    'strike': (),
    'strong': (),
    'img': ('src', 'width', 'height', 'border', 'alt', 'title'),
    'u': (),
}


class MarkdownRenderer(BaseRenderer):
    label = ugettext_lazy(u'Markdown')

    reference = '<a href="http://en.wikipedia.org/wiki/Markdown" target="_blank">%s</a>' % (ugettext_lazy(u'Markdown'))

    def render(self, text):
        return sph_markdown(text)


AVAILABLE_MARKUP = {
    'bbcode': BBCodeRenderer,
    'markdown': MarkdownRenderer
}


def _get_markup_choices():
    choices = []
    classes = {}

    enabled_markup = get_sph_setting('board_markup_enabled', ('bbcode',))
    custom_markup = get_sph_setting('board_custom_markup', {})

    for en in enabled_markup:
        try:
            renderclass = AVAILABLE_MARKUP[en]
        except KeyError:
            try:
                renderer = custom_markup[en]
            except KeyError:
                raise exceptions.ImproperlyConfigured(
                    _(u"Custom renderer '%(renderer)s' needs a matching Render \
Class entry in your sphene settings 'board_custom_markup'") \
                    % {'renderer': en})
            renderclass = get_method_by_name(renderer)

        classes[en] = renderclass

        choices.append((en, renderclass.label))

    return tuple(choices), classes


POST_MARKUP_CHOICES, RENDER_CLASSES = _get_markup_choices()


def render_body(body, markup=None, apply_spammer_limits=False):
    """ Renders the given body string using the given markup.
    """
    if markup:
        try:
            renderer = RENDER_CLASSES[markup]()
            return renderer.render(body, apply_spammer_limits)
        except KeyError:
            raise exceptions.ImproperlyConfigured(
                _(u"Can't render markup '%(markup)s'") % {'markup': markup})
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

    return ugettext_lazy('You can use %(description)s in your posts') % {'description': desc}
