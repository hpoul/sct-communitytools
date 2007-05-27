from django import template
from django.conf import settings
from time import strftime
import re

from sphene.community.sphutils import HTML, get_sph_setting

from sphene.contrib.libs.markdown import mdx_macros

register = template.Library()


class SimpleHelloWorldMacro (object):
    def handleMacroCall(self, doc, params):
        return doc.createTextNode("Hello World!")

import urllib2
from django.core.cache import cache

class IncludeMacro (mdx_macros.PreprocessorMacro):
    def handlePreprocessorMacroCall(self, params):
        if params.has_key( 'url' ):
            cache_key = 'sph_community_includemacro_' + params['url'] + '_' + params.get( 'start', '' ) + '_' + params.get( 'end', '' );
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

class NewsMacro (object):
    """
    displays threads in the given board category
    """
    def handleMacroCall(self, doc, params):
        from sphene.sphboard.models import Post

        if not params.has_key( 'category' ):
            return doc.createTextNode("Error, no 'category' or 'template' given for news macro.")

        limit = 'limit' in params and params['limit'] or 5
        templateName = 'wiki/news.html'
        if params.has_key( 'template' ): templateName = params['template']
        
        threads = Post.objects.filter( category__id = params['category'], thread__isnull = True ).order_by( '-postdate' )[:limit]

        t = template.loader.get_template( templateName )
        baseURL = ''
        if params.has_key( 'baseURL' ): baseURL = params['baseURL']
        c = template.Context({ 'threads': threads,
                               'baseURL': baseURL,
                               })
        
        return HTML( t.render(c) )


        

from sphene.community.middleware import get_current_sphdata, get_current_group


@register.filter
def sph_markdown(value, arg='', oldmd=None, extra_macros={}):
    try:
        from sphene.contrib.libs.markdown import markdown
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError, "Error in {% markdown %} filter: The Python markdown library isn't installed."
        return value
    else:
        save_mode = arg == 'safe'
        macros = { 'helloWorld': SimpleHelloWorldMacro(),
                   'news': NewsMacro(),
                   'include': IncludeMacro(),
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
                                 )
        md.header_numbering = get_sph_setting('markdown_header_numbering', True)
        md.header_numbering_start = get_sph_setting('markdown_header_numbering_start', 1)
        if oldmd and hasattr(oldmd,'header_numbers'): md.header_numbers = oldmd.header_numbers
        ret = md.toString()
        if hasattr(md, 'tocDiv'):
            sphdata = get_current_sphdata()
            sphdata['toc'] = md.tocDiv.toxml()
        return ret

from sphene.community.sphutils import get_fullusername, format_date

@register.filter
def sph_date(value):
    return format_date(value)


@register.filter
def sph_fullusername(value):
    """ returns the full username of the given user - if defined
    (No HTML, just text) """
    return get_fullusername(value)

import os

@register.filter
def sph_basename(value):
    basename = os.path.basename( value )
    return basename
