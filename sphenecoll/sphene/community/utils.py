

def get_fullusername(value):
    """ returns the full username of the given user - if defined
    (No HTML, just text) """
    if not value: return "(Error)"
    if not value.first_name or not value.last_name:
        return value.username
    return "%s %s" % (value.first_name, value.last_name)


def format_date(value):
    return value.strftime( "%Y-%m-%d %H:%M:%S" )


from django.contrib.auth.models import User

def get_user_link_for_username(username):
    try:
        user = User.objects.get( username__exact = username )
    except User.DoesNotExist:
        return username
    # TODO add a link to user profiles
    return get_fullusername(user)

