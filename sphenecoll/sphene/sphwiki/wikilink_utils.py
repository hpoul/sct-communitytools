
import re
from sphene.sphwiki.models import WikiSnip
from sphene.community.sphutils import get_sph_setting
from sphene.community.middleware import get_current_group

WIKILINK_RE = r'''(?P<escape>\\|\b)?(?P<wholeexpression>(((?P<camelcase>([A-Z]+[a-z-_0-9]+){2,})\b)|\[(?P<snipname>[A-Za-z-_/0-9]+)(\|(?P<sniplabel>.+?))?\]))'''

WIKILINK_RE = get_sph_setting( 'wikilink_regexp', WIKILINK_RE )

WIKILINK_RE_COMPILED = re.compile(WIKILINK_RE)

def get_wikilink_regex_pattern():
    return WIKILINK_RE

def get_wikilink_regex():
    return WIKILINK_RE_COMPILED


def handle_wikilinks_match(matchgroups):
    if matchgroups.get('escape'): return { 'label': matchgroups.get('wholeexpression') }
    snipname = matchgroups.get('camelcase') or matchgroups.get('snipname')
    label = matchgroups.get('sniplabel') or snipname.replace('_', ' ')

    cssclass = 'sph_wikilink'

    try:
        snip = WikiSnip.objects.get( group = get_current_group(),
                                     name = snipname, )
        href = snip.get_absolute_url()
    except WikiSnip.DoesNotExist:
        
        snip = WikiSnip( group = get_current_group(),
                         name = snipname, )

        if not snip.has_edit_permission() \
                and get_sph_setting('wiki_links_nonexistent_show_only_privileged'):
            return { 'label': label, }

        href = snip.get_absolute_editurl()
        cssclass += ' sph_nonexistent'
        if get_sph_setting( 'wiki_links_nonexistent_prefix' ):
            label = "create:"+label
    
    return { 'href': href,
             'label': label,
             'class': cssclass,
             }

def render_wikilinks_match(match):
    wikilink = handle_wikilinks_match(match.groupdict())
    if not 'href' in wikilink: return wikilink['label']
    return '''<a href="%s" class="%s">%s</a>''' % (wikilink['href'], wikilink['class'], wikilink['label'])

def render_wikilinks(source):
    done = WIKILINK_RE_COMPILED.sub( render_wikilinks_match, source )
    return done

