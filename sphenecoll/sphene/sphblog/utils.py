
# Copied from http://www.djangosnippets.org/snippets/369/

import re
import unicodedata
from htmlentitydefs import name2codepoint
from django.utils.encoding import smart_unicode, force_unicode
from slughifi import slughifi


def slugify(s, entities=True, decimal=True, hexadecimal=True, model=None, slug_field='slug', pk=None):
    s = smart_unicode(s)
    # we don't want a string > 40 characters
    if len(s) > 40:
        s = s[:40]

    s = slughifi(s)

    slug = s
    if model:  
        # return unique slug for a model (appending integer counter)
        def get_query():
            query = model.objects.filter(**{ slug_field: slug })
            if pk:
                query = query.exclude(pk=pk)
            return query
        counter = 2
        while get_query():
            slug = "%s-%s" % (s, counter)
            counter += 1
    return slug
