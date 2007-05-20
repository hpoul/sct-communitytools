#!/usr/bin/env python

'''
WikiLink Extention for Python-Markdown
======================================

Converts CamelCase words to relative links.  Requires Python-Markdown 1.6+

Basic usage:

    >>> import markdown
    >>> text = "Some text with a WikiLink."
    >>> md = markdown.markdown(text, ['wikilink'])
    >>> md
    '\\n<p>Some text with a <a href="/WikiLink/" class="wikilink">WikiLink</a>.\\n</p>\\n\\n\\n'

To define custom settings the simple way:

    >>> md = markdown.markdown(text, 
    ...     ['wikilink(base_url=/wiki/,end_url=.html,html_class=foo)']
    ... )
    >>> md
    '\\n<p>Some text with a <a href="/wiki/WikiLink.html" class="foo">WikiLink</a>.\\n</p>\\n\\n\\n'
    
Custom settings the complex way:

    >>> md = markdown.Markdown(text, 
    ...     extensions = ['wikilink'], 
    ...     extension_configs = {'wikilink': [
    ...                                 ('base_url', 'http://example.com/'), 
    ...                                 ('end_url', '.html'),
    ...                                 ('html_class', '') ]},
    ...     encoding='utf8',
    ...     safe_mode = True)
    >>> str(md)
    '\\n<p>Some text with a <a href="http://example.com/WikiLink.html">WikiLink</a>.\\n</p>\\n\\n\\n'

From the command line:

    python markdown.py -x wikilink(base_url=http://example.com/,end_url=.html,html_class=foo) src.txt

By [Waylan Limberg](http://achinghead.com/).

Project website: http://achinghead.com/markdown-wikilinks/
Contact: waylan [at] gmail [dot] com

License: [BSD](http://www.opensource.org/licenses/bsd-license.php) 

Version: 0.4 (Oct 14, 2006)

Dependencies:
* [Python 2.3+](http://python.org)
* [Markdown 1.6+](http://www.freewisdom.org/projects/python-markdown/)
* For older dependencies use [WikiLink Version 0.3]
(http://code.limberg.name/svn/projects/py-markdown-ext/wikilinks/tags/release-0.3/)


2007-04-14 herbert.poul@gmail.com:
Made quite some changes.. and externalized most part of creating wiki links to another class..
so this is not longer an independent implementation but bound into SCT.
'''

import markdown
import re
from sphene.sphwiki import wikilink_utils

class WikiLinkExtension (markdown.Extension) :
    def __init__(self, configs):
        # set extension defaults
        self.config = {
                        'base_url' : ['/', 'String to append to beginning or URL.'],
                        'end_url' : ['/', 'String to append to end of URL.'],
                        'html_class' : ['wikilink', 'CSS hook. Leave blank for none.'],
                        'callback' : [None, 'Callback method which is called when creating a link.'],
        }
        
        # Override defaults with user settings
        for key, value in configs :
            # self.config[key][0] = value
            self.setConfig(key, value)
        
    def extendMarkdown(self, md, md_globals):
        self.md = md
        #md.registerExtension(self) #???
    
        # append to end of inline patterns
        #WIKILINK_RE = r'''(((?P<escape>\\|\b)(?P<camelcase>([A-Z]+[a-z-_]+){2,})\b)|\[(?P<snipname>[A-Za-z-_/]+)(\|(?P<sniplabel>[\w \-]+?))?\])'''
        md.inlinePatterns.append(WikiLinks(wikilink_utils.get_wikilink_regex_pattern(), self.config))

class WikiLinks (markdown.BasePattern) :
    def __init__(self, pattern, config):
        markdown.BasePattern.__init__(self, pattern)
        self.config = config
        self.compiled_re = re.compile("^(.*?)%s(.*?)$" % pattern, re.DOTALL)
  
    def handleMatch(self, m, doc) :
        wikilink = wikilink_utils.handle_wikilinks_match(m.groupdict())
        if not 'href' in wikilink: return doc.createTextNode(wikilink['label'])

        a = doc.createElement('a')
        a.appendChild(doc.createTextNode(wikilink['label']))
        a.setAttribute('href', wikilink['href'])
        a.setAttribute('class', wikilink['class'])

        return a
    
def makeExtension(configs=None) :
    return WikiLinkExtension(configs=configs)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
