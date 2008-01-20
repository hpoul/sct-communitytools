
from sphene.community.middleware import get_current_sphdata


def add_rss_feed(url, label):
    sphdata = get_current_sphdata()
    if not 'rss' in sphdata:
        sphdata['rss'] = []

    sphdata['rss'].append( { 'url': url,
                             'label': label, } )
    
