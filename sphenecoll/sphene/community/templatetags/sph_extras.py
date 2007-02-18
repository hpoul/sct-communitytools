from django import template
from time import strftime
import re

from sphene.sphwiki.models import WikiAttachment
from sphene.sphboard.models import Category, Post

register = template.Library()

class SimpleHelloWorldMacro (object):
    def handleMacroCall(self, doc, params):
        return doc.createTextNode("Hello World!")

class ImageMacro (object):
    def handleMacroCall(self, doc, params):
        if params.has_key( 'id' ):
            attachment = WikiAttachment.objects.get( id = params['id'] )
            el = doc.createElement( 'img' )
            el.setAttribute( 'src', attachment.get_fileupload_url() )
            for paramName in [ 'width', 'height', 'alt', 'align' ]:
                if params.has_key( paramName ):
                    el.setAttribute( paramName, params[paramName] )
            return el
        return doc.createTextNode("Error, no 'id' given for img macro.")

import urllib2

class IncludeMacro (object):
    def handleMacroCall(self, doc, params):
        if params.has_key( 'url' ):
            f = urllib2.urlopen( params['url'] )
            try:
                text = f.read()
                return HTML( sph_markdown( text ) )
            finally:
                f.close()
        return doc.createTextNode("Error, no 'url' given for include macro.")

class HTML:
    type = "text"
    attrRegExp = re.compile(r'\{@([^\}]*)=([^\}]*)}') # {@id=123}
    
    def __init__(self, value):
        self.value = value

    def attributeCallback(self, match) :
        self.parent.setAttribute(match.group(1), match.group(2))
        
    def handleAttributes(self) :
        self.value = self.attrRegExp.sub(self.attributeCallback, self.value)

    def toxml(self):
        return self.value

"""
displays threads in the given board category
"""
class NewsMacro (object):
   def handleMacroCall(self, doc, params):
       if not params.has_key( 'category' ):
           return doc.createTextNode("Error, no 'category' or 'template' given for news macro.")

       templateName = 'wiki/news.html'
       if params.has_key( 'template' ): templateName = params['template']

       threads = Post.objects.filter( category__id = params['category'], thread__isnull = True )

       t = template.loader.get_template( templateName )
       baseURL = ''
       if params.has_key( 'baseURL' ): baseURL = params['baseURL']
       c = template.Context({ 'threads': threads,
                              'baseURL': baseURL,
                              })
       
       return HTML( t.render(c) )

@register.filter
def sph_markdown(value, arg=''):
    try:
        import markdown
    except ImportError:
        if settings.DEBUG:
            raise template.TemplateSyntaxError, "Error in {% markdown %} filter: The Python markdown library isn't installed."
        return value
    else:
        save_mode = arg == 'safe'
        md = markdown.Markdown(value,
                               extensions = [ 'footnotes', 'wikilink', 'macros' ],
                               extension_configs = { 'wikilink': [ ( 'base_url', '../' ),
                                                                   ],
                                                     'macros': [ ( 'macros',
                                                                   { 'helloWorld': SimpleHelloWorldMacro(),
                                                                     'img': ImageMacro(),
                                                                     'news': NewsMacro(),
                                                                     'include': IncludeMacro(), } )]},
                                 )
        return md.toString()

@register.filter
def sph_date(value):
    return value.strftime( "%Y-%m-%d %H:%M:%S" )

