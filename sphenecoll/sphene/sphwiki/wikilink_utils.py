
import re
from sphene.sphwiki.models import WikiSnip
from sphene.community.sphutils import get_sph_setting
from sphene.community.middleware import get_current_group

WIKILINK_RE = r'''(?P<escape>\\|\b)?(?P<wholeexpression>(((?P<camelcase>([A-Z]+[a-z-_]+){2,})\b)|\[(?P<snipname>[A-Za-z-_/]+)(\|(?P<sniplabel>.+?))?\]))'''

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
    try:
        snip = WikiSnip.objects.get( group = get_current_group(),
                                     name = snipname, )
        href = snip.get_absolute_url()
    except WikiSnip.DoesNotExist:
        snip = WikiSnip( group = get_current_group(),
                         name = snipname, )
        href = snip.get_absolute_editurl()
        label = "create:"+label
    
    return { 'href': href,
             'label': label,
             'class': 'sph_wikilink',
             }

def render_wikilinks_match(match):
    wikilink = handle_wikilinks_match(match.groupdict())
    if not 'href' in wikilink: return wikilink['label']
    return '''<a href="%s" class="%s">%s</a>''' % (wikilink['href'], wikilink['class'], wikilink['label'])

def render_wikilinks(source):
    done = WIKILINK_RE_COMPILED.sub( render_wikilinks_match, source )
    return done

