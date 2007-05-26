


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
            if type(urlconf) != list:
                # If type is no list, we assume it is a request object and
                # look for a 'urlconf' attribute
                urlconf = getattr(urlconf, 'urlconf', None)
        
        bits = func(*args, **kwargs)
        viewname = bits[0]
        return reverse(bits[0], urlconf, *bits[1:3])
    return inner


def get_fullusername(value):
    """ returns the full username of the given user - if defined
    (No HTML, just text) """
    if not value: return "Anonymous"
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

usecaptcha = True
try:
    from djaptcha.models import CaptchaRequest, CAPTCHA_ANSWER_OK
    #from django.db.models import permalink
    from sphene.community.middleware import get_current_request, get_current_group

    def captcha_request_get_absolute_url(self):
        return ('sphene.community.views.captcha_image', (), { 'token_id': self.id })
    get_absolute_captcha_url = sphpermalink(captcha_request_get_absolute_url, get_current_request)
    
    usecaptcha = True
except:
    usecaptcha = False

from random import random

def has_captcha_support():
    """ Determines if captcha support is currently enabled. """
    return usecaptcha

def generate_captcha():
    """
    Generates a captcha. and returns an object which has a method
    get_absolute_url() which returns the url to the captcha image and
    a attribute 'uid' which contains the id of the captcha.
    """
    if not usecaptcha: return None
    numbers = (int(random()*9)+1,int(random()*9)+1)
    text = "%d+%d" % numbers
    answer = sum(numbers)
    req = CaptchaRequest.generate_request(text,answer,get_current_request().path)
    return req

def validate_captcha(id, answer):
    """
    Validates a given captcha and returns True if the answer is correct, False otherwise.
    """
    if not usecaptcha: return True
    captcha = CaptchaRequest.objects.get(pk = id)
    return captcha.answer == answer
    return False
#return CaptchaRequest.validate(uid, answer) == CAPTCHA_ANSWER_OK


from django import newforms as forms

class CaptchaInputWidget(forms.widgets.TextInput):

    def render(self, name, value, attrs=None):
        return u'<span class="sph_captcha"><img src="%s" alt="Captcha Input" /> %s</span>' % (value, super(CaptchaInputWidget, self).render(name, None, attrs))

class CaptchaWidget(forms.widgets.MultiWidget):
    def __init__(self, attrs=None):
        widgets = (forms.HiddenInput(attrs=attrs), CaptchaInputWidget(attrs=attrs))
        super(CaptchaWidget, self).__init__(widgets, attrs)

    def render(self, name, value, attrs=None):
        req = generate_captcha()
        value = [req.id, get_absolute_captcha_url(req)]
        return super(CaptchaWidget, self).render(name, value, attrs)

    def decompress(self, value):
        return None

class CaptchaField(forms.fields.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (forms.fields.CharField(), forms.fields.CharField(), )
        super(CaptchaField, self).__init__(fields, *args, **kwargs)

    def clean(self, value):
        super(CaptchaField, self).clean(value)
        if not validate_captcha(value[0], int(value[1])):
            raise forms.ValidationError(u'Invalid Captcha response.')
        
    def compress(self, data_list):
        return None


