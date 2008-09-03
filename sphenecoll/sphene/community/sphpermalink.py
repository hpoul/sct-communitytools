from django.core.urlresolvers import reverse



# Decorator. Takes a function that returns a tuple in this format:
#     (viewname, viewargs, viewkwargs)
#   Optionally takes a function which should either return an object with
#     an attribute 'urlconf' or directly a python list which is used instead of
#     settings.ROOT_URLCONF
# Returns a function that calls urlresolvers.reverse() on that data, to return
# the URL for those parameters.
def sphpermalink(func, get_urlconf_func = None):
    from django.core.urlresolvers import reverse
    def inner(*args, **kwargs):
        # Find urlconf ...
        urlconf = None
        if get_urlconf_func != None:
            urlconf = get_urlconf_func()
            if hasattr(urlconf, 'urlconf'):
                # If type is no list, we assume it is a request object and
                # look for a 'urlconf' attribute
                urlconf = getattr(urlconf, 'urlconf', None)
        
        bits = func(*args, **kwargs)
        viewname = bits[0]
        # OMG that is an ugly hack !!
        if 'groupName' in bits[2]:
            del bits[2]['groupName']

        if not hasattr( urlconf, '__iter__' ) \
                and not isinstance( urlconf, str ):
            # If urlconf is not a list / tuple set it to None.
            urlconf = None

        return reverse(bits[0], urlconf, *bits[1:3])
    return inner


def get_urlconf():
    from sphene.community.middleware import get_current_request
    return getattr(get_current_request(), 'urlconf', None)

