import logging
import os
import urllib
import requests
from base64 import b64encode

from django import template
from django.conf import settings

from sphene.community import sphsettings

register = template.Library()
logger = logging.getLogger(__name__)

@register.filter
def website_thumbnail_url(url, width):
    width = str(width)
    type = 'jpg'
    cache_root = os.path.join('cache', 'sphlinklist', 'thumbnail')
    cache_key = '%s.%s' % (b64encode(':'.join([url, width]).encode('utf-8')).decode('utf-8'), type)
    cache_path = os.path.join(cache_root, cache_key)
    local_cache_file = os.path.join(settings.MEDIA_ROOT, cache_path)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, cache_root), exist_ok=True)
    if not os.path.exists(local_cache_file):
        logger.debug('Downloading thumbnail for url %s into %s', url, local_cache_file)
        apikey = sphsettings.get_sph_setting('sphlinklist_thumbnail.ws_apikey')
        response = requests.get('https://api.thumbnail.ws/api/%s/thumbnail/get' % apikey,
                                params={'url': url, 'width': width}
                                )
        with open(local_cache_file, 'wb') as buf:
            buf.write(response.content)

    return { 'url': settings.MEDIA_URL + cache_path }
