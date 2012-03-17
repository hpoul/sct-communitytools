import re
import logging

from django.conf import settings
from django.core import exceptions
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import loader
from django.utils.translation import ugettext as _
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.core.cache import cache

from sphene.community.middleware import get_current_request, get_current_sphdata, get_current_group
from sphene.community.sphpermalink import sphpermalink as imported_sphpermalink
from sphene.community import sphsettings

logger = logging.getLogger('sphene.community.sphutils')


# For backward compatibility .. it has been moved into it's own module file.
sphpermalink = imported_sphpermalink

def get_urlconf():
    request = get_current_request()
    return getattr(request, 'urlconf', None)


def get_user_displayname(user):
    """ returns the full username of the given user - if defined
    (No HTML, just text) """
    if not user: return _(u"Anonymous")
    key = '%s_%s' % (settings.CACHE_MIDDLEWARE_KEY_PREFIX, user.pk)
    res = cache.get(key)
    if not res:
        get_displayname = get_sph_setting( 'community_user_get_displayname' )
        if get_displayname is not None:
            res = get_displayname(user)

        if res is None:
            profile = user.communityuserprofile_set.all()
            if profile and profile[0].displayname:
                res = profile[0].displayname
            elif (not user.first_name or not user.last_name) or\
                    get_sph_setting( 'community_user_displayname_fallback' ) == 'username':
                res = user.username
            else:
                res = "%s %s" % (user.first_name, user.last_name)
        cache.set(key, res)
    return res

# This is for backwards compatibility
get_fullusername = get_user_displayname

def format_date(value, format = None):
    if not hasattr(value, 'strftime') :
        logger.error( 'Wrong value to format date: %s' % (str(value)) )
	return str(value)
    if format is None:
        format = 'FULL_DATE'

    if format == 'ONLY_DATE':
        return value.strftime( "%Y-%m-%d")

    return value.strftime( "%Y-%m-%d %H:%M:%S" )


from django.contrib.auth.models import User

def get_user_link_for_username(username):
    try:
        user = User.objects.get( username__exact = username )
    except User.DoesNotExist:
        return username
    # TODO add a link to user profiles
    return get_user_displayname(user)

def render_blockquote(citation, membername, post):
    memberlink = get_user_link_for_username(membername)
    return loader.render_to_string('sphene/community/_display_blockquote.html',
                                    {'citation':mark_safe(citation),
                                     'post':post,
                                     'memberlink':memberlink})

usecaptcha = True
try:
    from djaptcha.models import CaptchaRequest, CAPTCHA_ANSWER_OK
    #from django.db.models import permalink
    from sphene.community.middleware import get_current_request

    def captcha_request_get_absolute_url(self):
        return ('sphene.community.views.captcha_image', (), { 'token_id': self.id })
    get_absolute_captcha_url = sphpermalink(captcha_request_get_absolute_url)
    
    # update the captcha settings defaults (which can still be overridden by a set_sph_setting)
    sphsettings.add_setting_defaults({'community_email_anonymous_require_captcha': True})

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


from django import forms

class CaptchaInputWidget(forms.widgets.TextInput):

    def render(self, name, value, attrs=None):
        return u'<span class="sph_captcha"><img src="%s" alt="%s" /> %s</span>' % (value, _(u'Captcha input'), super(CaptchaInputWidget, self).render(name, None, attrs))

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
        intval = None
        try:
            intval = int(value[1])
        except ValueError:
            # Input was no valid integer value
            pass

        if intval is None or not validate_captcha(value[0], int(value[1])):
            raise forms.ValidationError(_(u'Invalid Captcha response.'))
        
    def compress(self, data_list):
        return None




class HTML:
    """
    Used as a dummy markdown entity which simply contains rendered HTML content.
    """
    type = "text"
    attrRegExp = re.compile(r'\{@([^\}]*)=([^\}]*)}') # {@id=123}
    
    def __init__(self, value):
        self.value = value

    def attributeCallback(self, match) :
        self.parent.setAttribute(match.group(1), match.group(2))
        
    def handleAttributes(self) :
        self.value = self.attrRegExp.sub(self.attributeCallback, self.value)

    def toxml(self):
        return self.value

def add_setting_defaults(newdefaults):
    """
    This method can be used by other applications to define their
    default values.
    
    newdefaults has to be a dictionary containing name -> value of
    the settings.
    """
    sphsettings.add_setting_defaults(newdefaults)

def get_sph_setting(name, default_value = None):
    return sphsettings.get_sph_setting(name, default_value)


class SphSettings(object):
    """
    Simple class which can be put into the django context to retrieve settings.
    """

    def __getattribute__(self, name):
        return get_sph_setting(name)

def sph_reverse( viewname, args=(), kwargs={} ):
    req = get_current_request()
    urlconf = getattr(req, 'urlconf', None)
    sphdata = get_current_sphdata()
    if 'group_fromhost' in sphdata and \
            not sphdata.get('group_fromhost', False):
        kwargs['groupName'] = get_current_group().name
    elif 'groupName' in kwargs:
        del kwargs['groupName']
    return reverse( viewname, urlconf, args, kwargs )

def get_method_by_name(methodname):
    """Import a named method from a string.  
    Usually used to load a method configured in settings.
    """
    try:
        dot = methodname.rindex('.')
    except ValueError:
        raise exceptions.ImproperlyConfigured, '%s isn\'t a module' % methodname
    named_module, named_method = methodname[:dot], methodname[dot+1:]
    try:
        named_mod = __import__(named_module, {}, {}, [''])
    except ImportError, e:
        raise exceptions.ImproperlyConfigured(
            'Error importing named method %s: "%s"' % (named_module, e))
    try:
        named_method = getattr(named_mod, named_method)
    except AttributeError:
        raise exceptions.ImproperlyConfigured(
            'Named module "%s" does not define a "%s" method' 
            % (named_module, named_method))

    return named_method

def add_rss_feed(url, label):
    sphdata = get_current_sphdata()
    if not 'rss' in sphdata:
        sphdata['rss'] = []

    sphdata['rss'].append( { 'url': url,
                             'label': label, } )

def sph_render_to_response(template_name, context = None):
    return render_to_response(template_name,
                              context,
                              context_instance = RequestContext(get_current_request()))


def include_js(jspath, prefix = None):
    jsincludes = get_sph_setting( 'community_jsincludes', [])

    if jspath in jsincludes:
        return

    if prefix is None:
        prefix = settings.STATIC_URL
    jsincludes.append(prefix + jspath)

    sphsettings.set_sph_setting( 'community_jsincludes', jsincludes )


def include_css(csspath, prefix = None):
    styleincludes = sphsettings.get_sph_setting( 'community_styleincludes', [])

    if csspath in styleincludes:
        return

    if prefix is None:
        prefix = settings.STATIC_URL
    styleincludes.append(prefix + csspath)
    sphsettings.set_sph_setting( 'community_styleincludes', styleincludes )


