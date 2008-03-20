# Create your views here.
from django import newforms as forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, HttpResponsePermanentRedirect, HttpResponseGone
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template import loader, Context
from django.core.mail import send_mail
from django.dispatch import dispatcher
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from sphene.community import PermissionDenied, sphsettings
from sphene.community.models import Role, RoleMember, RoleMemberLimitation, PermissionFlag, TagLabel, TaggedItem
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display
from sphene.community.sphutils import sph_reverse
from sphene.community.templatetags.sph_extras import sph_user_profile_link
from sphene.community.middleware import get_current_sphdata
from sphene.contrib.libs.common.utils.misc import cryptString, decryptString


class RegisterEmailAddress(forms.Form):
    email_address = forms.EmailField(label=_(u'Email address'))
    
    def clean(self):
        if 'email_address' not in self.cleaned_data:
            return self.cleaned_data

        if User.objects.filter( email__exact = self.cleaned_data['email_address'] ).count() != 0:
            raise forms.ValidationError(_(u"Another user is already registered with the email address %(email)s.")
                                        % {'email':self.cleaned_data['email_address']} )
        return self.cleaned_data

from django.contrib.auth.views import login as view_login, logout as view_logout
from django.contrib.auth import REDIRECT_FIELD_NAME

def accounts_login(request, group = None):
    return view_login( request, template_name = 'sphene/community/accounts/login.html', )

def accounts_logout(request, group = None):
    sphdata = get_current_sphdata()
    sphdata['is_logout'] = True
    return view_logout( request, template_name = 'sphene/community/accounts/logged_out.html', )


class ForgotUsernamePassword(forms.Form):
    email_address = forms.EmailField(label=_(u'Email address'))

    def clean_email_address(self):
        try:
            user = User.objects.get( email__exact = self.cleaned_data['email_address'] )
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            raise forms.ValidationError( _(u'No user found with that email address.') )
        return self.cleaned_data

from random import choice
import string
def generate_password():
    chars = string.letters + string.digits
    newpassword = ''
    for i in range(10):
        newpassword = newpassword + choice(chars)
    return newpassword

def accounts_forgot(request, group = None):
    if request.method == 'POST':
        form = ForgotUsernamePassword(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = data['user']

            password = generate_password()
            user.set_password(password)
            user.save()
            if not group:
                subject = _(u'Your requested username / password')
            else:
                subject = _(u'Your requested username / password for site %(site_name)s') % {'site_name': group.get_name()}
            t = loader.get_template('sphene/community/accounts/forgot_password_email.txt')
            c = {
                'currentuser': user,
                'password': password,
                }
            body = t.render(RequestContext(request, c))

            send_mail( subject, body, None, [user.email] )
            return render_to_response( 'sphene/community/accounts/forgot_sent.html',
                                       { },
                                       context_instance = RequestContext(request) )
    else:
        form = ForgotUsernamePassword()
    return render_to_response( 'sphene/community/accounts/forgot.html',
                               { 'form': form,
                                 },
                               context_instance = RequestContext(request) )

def register(request, group = None):

    if request.method == 'POST':
        form = RegisterEmailAddress(request.POST)
        if form.is_valid():
            regdata = form.cleaned_data
            email_address = regdata['email_address']
            if not group:
                subject = _(u'Email verification required')
            else:
                subject = _(u'Email verification required for site %(site_name)s') % {'site_name': group.get_name()}
            validationcode = cryptString( settings.SECRET_KEY, email_address )
            t = loader.get_template('sphene/community/accounts/account_verification_email.txt')
            c = {
                'email': email_address,
                'baseurl': group.baseurl,
                'path': sph_reverse( 'sphene.community.views.register_hash', (), { 'emailHash': validationcode, } ),
                'validationcode': validationcode,
                'group': group,
                }
            send_mail( subject, t.render(RequestContext(request, c)), None, [email_address] )
            return render_to_response( 'sphene/community/register_emailsent.html',
                                       { 'email': email_address,
                                         },
                                       context_instance = RequestContext(request) )
        pass
    else:
        form = RegisterEmailAddress()

    return render_to_response( 'sphene/community/register.html',
                               { 'form': form },
                               context_instance = RequestContext(request) )

username_re = r'^\w+$'

class RegisterForm(forms.Form):
    username = forms.RegexField( username_re, label=_(u'Username'))
    email_address = forms.CharField(label=_(u'Email address'),
                                    widget = forms.TextInput(attrs={'disabled': 'disabled'}))
    password = forms.CharField(label=_(u'Password'),
                               widget = forms.PasswordInput )
    repassword = forms.CharField(label=_(u'Verify Password'),
                                 widget = forms.PasswordInput )

    def clean(self):
        if not 'password' in self.cleaned_data or not 'repassword' in self.cleaned_data:
            return self.cleaned_data
        
        if self.cleaned_data['password'] != self.cleaned_data['repassword']:
            raise forms.ValidationError(_(u'Passwords do not match.'))

        return self.cleaned_data

    def clean_username(self):
        if User.objects.filter( username__exact = self.cleaned_data['username'] ).count() != 0:
            raise forms.ValidationError(_(u'The username %(username)s is already taken.') % {'username': self.cleaned_data['username']})
        return self.cleaned_data['username']

    def clean_email_address(self):
        if User.objects.filter( email__exact = self.cleaned_data['email_address'] ).count() != 0:
            raise forms.ValidationError(_(u'Another user is already registered with the email address %(email)s.')
                                        % {'email':self.cleaned_data['email_address']} )
        return self.cleaned_data['email_address']


def register_hash(request, emailHash, group = None):
    email_address = decryptString( settings.SECRET_KEY, emailHash )
    if request.method == 'POST':
        post = request.POST.copy()
        post.update( { 'email_address': email_address } )
        form = RegisterForm( post )
        if form.is_valid():
            formdata = form.cleaned_data
            user = User.objects.create_user( formdata['username'],
                                             formdata['email_address'],
                                             formdata['password'], )
            user = authenticate( username = formdata['username'], password = formdata['password'] )
            login(request, user)
            return render_to_response( 'sphene/community/register_hash_success.html',
                                       { },
                                       context_instance = RequestContext(request) )
    else:
        form = RegisterForm( )
        form.fields['email_address'].initial = email_address
    return render_to_response( 'sphene/community/register_hash.html',
                               { 'form': form },
                               context_instance = RequestContext(request) )





##############################################################
####
#### The following code was copied from the django captchas project.
#### and slightly modified.

from django.http import HttpResponse
try:

    from djaptcha.models import CaptchaRequest
    from cStringIO import StringIO
    import random
    import Image,ImageDraw,ImageFont
    
except:
    pass

# You need to get the font from somewhere and have it accessible by Django
# I have it set in the djaptcha's settings dir
#from django.conf.settings import FONT_PATH,FONT_SIZE

def captcha_image(request,token_id,group = None):
    """
    Generate a new captcha image.
    """
    captcha = CaptchaRequest.objects.get(id=token_id)
    text = captcha.text
    #TODO: Calculate the image dimensions according to the given text.
    #      The dimensions below are for a "X+Y" text
    image = Image.new('RGB', (40, 23), (39, 36, 81))
    # You need to specify the fonts dir and the font you are going to usue
    font = ImageFont.truetype(settings.FONT_PATH,settings.FONT_SIZE)
    draw = ImageDraw.Draw(image)
    # Draw the text, starting from (2,2) so the text won't be edge
    draw.text((2, 2), text, font = font, fill = (153, 204, 0))
    # Saves the image in a StringIO object, so you can write the response
    # in a HttpResponse object
    out = StringIO()
    image.save(out,"JPEG")
    out.seek(0)
    response = HttpResponse()
    response['Content-Type'] = 'image/jpeg'
    response.write(out.read())
    return response


def profile(request, group, user_id):
    user = get_object_or_404(User, pk = user_id)
    has_edit_permission = False
    profile_edit_url = None

    if user == request.user:
        has_edit_permission = True
        profile_edit_url = sph_reverse( 'sphene.community.views.profile_edit', (), { 'user_id': user.id, })

    ret = dispatcher.send(signal = profile_display,
                          request = request,
                          user = user, )

    additionalprofile = ''
    blocks = list()
    for listener in ret:
        if listener[1]:
            response = listener[1]

            if isinstance( response, dict ):
                blocks.append(response['block'])
                response = response['additionalprofile']

            additionalprofile += response
    
    return render_to_response( 'sphene/community/profile.html',
                               { 'profile_user': user,
                                 'profile_blocks': blocks,
                                 'has_edit_permission': has_edit_permission,
                                 'profile_edit_url': profile_edit_url,
                                 'additionalprofile': mark_safe( additionalprofile ),
                                 },
                               context_instance = RequestContext( request ))

def profile_edit_mine(request, group):
    return profile_edit(request, group = group, user_id = None)


def profile_edit(request, group, user_id):
    if user_id:
        user = get_object_or_404(User, pk = user_id)
    else:
        user = request.user

    if user is None or user != request.user or not user.is_authenticated():
        raise PermissionDenied()

    if request.method == 'POST':
        reqdata = request.POST.copy()
        reqdata.update(request.FILES)
        form = EditProfileForm(user, request.POST, request.FILES)
    else:
        form = EditProfileForm(user)

    dispatcher.send(signal = profile_edit_init_form,
                    sender = EditProfileForm,
                    instance = form,
                    request = request,
                    )
    
    if request.method == 'POST':
        if form.is_valid():
            data = form.cleaned_data
            user.first_name = data['first_name']
            user.last_name = data['last_name']

            if user.email != data['email_address']:
                # Require email validation ...
                pass

            if data['new_password']:
                # Check was already made in form, we only need to change the password.
                user.set_password( data['new_password'] )

            dispatcher.send(signal = profile_edit_save_form,
                            sender = EditProfileForm,
                            instance = form,
                            request = request,
                            )
            

            user.save()
            request.user.message_set.create( message = _(u'Successfully changed user profile.') )
            
            return HttpResponseRedirect( sph_user_profile_link( user ) )

    else:
        form.fields['first_name'].initial = user.first_name
        form.fields['last_name'].initial = user.last_name
        form.fields['email_address'].initial = user.email

    
    """
    form = EditProfileForm( { 'first_name': user.first_name,
                              'last_name': user.last_name,
                              'email_address': user.email,
                              } )
    """
    
    return render_to_response( 'sphene/community/profile_edit.html',
                               { 'user': user,
                                 'form': form,
                                 },
                               context_instance = RequestContext(request) )



def admin_permission_role_list(request, group):
    roles = Role.objects.filter( group = group )
    return render_to_response( 'sphene/community/admin/permission/role_list.html',
                               { 'roles' : roles,
                                 },
                               context_instance = RequestContext(request) )

from forms import EditRoleForm

def admin_permission_role_edit(request, group, role_id = None):
    role = None
    if role_id:
        role = get_object_or_404(Role, pk = role_id)
        
    if request.method == 'POST':
        form = EditRoleForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            r = role
            if not r:
                r = Role(group = group)
            r.name = data['name']
            r.save()
            
            # Delete old flags
            r.permission_flags.clear()

            # Add all flags
            for flag_name in data['permission_flags']:
                r.permission_flags.add( PermissionFlag.objects.get( name = flag_name ) )

            r.save()

            request.user.message_set.create( message = _(u'Successfully saved role.') )
            return HttpResponseRedirect( r.get_absolute_memberlisturl() )
            
    else:
        form = EditRoleForm()

    if role:
        form.fields['name'].initial = role.name
        form.fields['permission_flags'].initial = [ flag.name for flag in role.permission_flags.all() ]
    
    return render_to_response( 'sphene/community/admin/permission/role_edit.html',
                               { 'form': form,
                                 },
                               context_instance = RequestContext(request) )

def admin_permission_role_member_list(request, group, role_id):
    role = get_object_or_404(Role, pk = role_id)
    members = role.rolemember_set.all()
    if 'cmd' in request.GET and request.GET['cmd'] == 'remove':
        memberid = request.GET['id']
        role_member = RoleMember.objects.get( pk = memberid )
        role_member.delete()

        request.user.message_set.create( message = _(u'Successfully deleted role member.') )

        return HttpResponseRedirect( role.get_absolute_memberlisturl() )
    return render_to_response( 'sphene/community/admin/permission/role_member_list.html',
                               { 'members': members,
                                 'role': role,
                                 },
                               context_instance = RequestContext(request) )

from forms import EditRoleMemberForm

def admin_permission_role_member_add(request, group, role_id):
    role = get_object_or_404(Role, pk = role_id)

    if request.method == 'POST':
        form = EditRoleMemberForm(group, request.POST)
        if form.is_valid():
            data = form.cleaned_data
            role_member = RoleMember( role = role,
                                      user = data['user'],
                                      has_limitations = data['has_limitations'], )
            role_member.save()
            if data['has_limitations']:
                limitation = RoleMemberLimitation( role_member = role_member,
                                                   object_type = data['object_type'],
                                                   object_id = data['object'], )
                limitation.save()
                
            request.user.message_set.create( message = _(u'Successfully added member.') )
            return HttpResponseRedirect( role.get_absolute_memberlisturl() )
    else:
        form = EditRoleMemberForm(group = group)
    
    return render_to_response( 'sphene/community/admin/permission/role_member_add.html',
                               { 'form': form,
                                 'role': role,
                                 },
                               context_instance = RequestContext(request) )

def groupaware_redirect_to(request, url, group, **kwargs):
    """
    Redirects either to the url given as 'url' or to a mapping defined in
    the SPH_SETTINGS variable 'community_groupaware_startpage'
    """
    group_name = group.name
    startpages = sphsettings.get_sph_setting('community_groupaware_startpage', None)
    if startpages is not None:
        if group_name in startpages:
            return HttpResponsePermanentRedirect(startpages[group_name] % kwargs)

    return HttpResponsePermanentRedirect(url % kwargs)

def tags_json_autocompletion(request, group):
    content_type_id = request.GET['content_type_id']
    tagstr = request.GET['string']

    from django.db import connection
    qn = connection.ops.quote_name
    taglabels = TagLabel.objects.filter( label__istartswith = tagstr,
                                         tag__group = group,
                                         ).extra(
        tables = [ TaggedItem._meta.db_table, ],
        where = [
            '%s.content_type_id = %%s' % qn( TaggedItem._meta.db_table ),
            '%s.tag_label_id = %s.%s' % ( qn( TaggedItem._meta.db_table ),
                                          qn( TagLabel._meta.db_table ),
                                          qn( TagLabel._meta.pk.column ) ) ],
        params = [ content_type_id ], )[:10]
    ret = ''
    for taglabel in taglabels:
        ret += '<taglabel><id>%d</id><label>%s</label><tag>%s</tag></taglabel>' % ( taglabel.id,
                                                                                    taglabel.label,
                                                                                    taglabel.tag.name )

    return HttpResponse("<taglabels>%s</taglabels>" % ret,
                        mimetype = 'text/xml', )



