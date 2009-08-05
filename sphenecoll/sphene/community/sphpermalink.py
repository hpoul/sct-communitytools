


# Decorator. Takes a function that returns a tuple in this format:
#     (viewname, viewargs, viewkwargs)
# Returns a function that calls urlresolvers.reverse() on that data, to return
# the URL for those parameters.
def sphpermalink(func):
    def inner(*args, **kwargs):
        from sphene.community.sphutils import sph_reverse
        # Find urlconf ...
        bits = func(*args, **kwargs)
        viewname, args, kwargs = bits

        return sph_reverse(viewname, args=args, kwargs=kwargs)
    return inner


def get_urlconf():
    from sphene.community.middleware import get_current_request
    return getattr(get_current_request(), 'urlconf', None)

