import urllib
# Create your views here.

from time import time
from urllib import quote, unquote
from hashlib import md5

from django.utils import simplejson

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse, HttpResponsePermanentRedirect, HttpResponseGone, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.template import loader, Context
from django.core.mail import send_mail, EmailMultiAlternatives
from django.contrib import messages
from django.contrib.auth import authenticate,login
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _, ugettext, ugettext_lazy
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse

from sphene.community import PermissionDenied, sphsettings
from sphene.community.models import Role, RoleMember, RoleMemberLimitation, PermissionFlag, TagLabel, TaggedItem, RoleGroup, RoleGroupMember
from sphene.community.forms import EditProfileForm, Separator, UsersSearchForm
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display
from sphene.community import sphutils
from sphene.community.permissionutils import has_permission_flag
from sphene.community.sphutils import sph_reverse
from sphene.community.templatetags.sph_extras import sph_user_profile_link
from sphene.community.middleware import get_current_sphdata
#from sphene.contrib.libs.common.utils.misc import cryptString, decryptString


class RegisterEmailAddress(forms.Form):
    email_address = forms.EmailField(label=ugettext_lazy(u'Email address'))
    captcha = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
                                    help_text = ugettext_lazy(u'Please enter the result of the above calculation.'),
                                    )
    
    def __init__(self, *args, **kwargs):
        super(RegisterEmailAddress, self).__init__(*args, **kwargs)
        if not sphutils.has_captcha_support() or not sphsettings.get_sph_setting('community_register_require_captcha', False):
            del self.fields['captcha']

    def clean(self):
        if 'email_address' not in self.cleaned_data:
            return self.cleaned_data

        if User.objects.filter( email__exact = self.cleaned_data['email_address'] ).count() != 0:
            raise forms.ValidationError(ugettext(u"Another user is already registered with the email address %(email)s.")
                                        % {'email':self.cleaned_data['email_address']} )
        return self.cleaned_data

from django.contrib.auth.views import login as view_login, logout as view_logout
from django.contrib.auth import REDIRECT_FIELD_NAME

def accounts_login(request, group = None):
    if request.user.is_authenticated() and 'next' in request.GET:
        return HttpResponseRedirect(request.GET['next'])
    return view_login( request, template_name = 'sphene/community/accounts/login.html', )

def accounts_logout(request, group = None):
    sphdata = get_current_sphdata()
    sphdata['is_logout'] = True
    return view_logout( request, template_name = 'sphene/community/accounts/logged_out.html', )


class ForgotUsernamePassword(forms.Form):
    email_address = forms.EmailField(label=ugettext_lazy(u'Email address'))

    def clean_email_address(self):
        try:
            user = User.objects.get( email__exact = self.cleaned_data['email_address'] )
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            raise forms.ValidationError( ugettext(u'No user found with that email address.') )
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
                subject = ugettext(u'Your requested username / password')
            else:
                subject = ugettext(u'Your requested username / password for site %(site_name)s') % {'site_name': group.get_name()}
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
                subject = ugettext(u'Email verification required')
            else:
                subject = ugettext(u'Email verification required for site %(site_name)s') % {'site_name': group.get_name()}
            validationcode = md5(settings.SECRET_KEY + email_address).hexdigest() ## cryptString( settings.SECRET_KEY, email_address )
            mail_context = RequestContext(request,
                                          {
                    'email': email_address,
                    'baseurl': group.baseurl,
                    'path': sph_reverse( 'sphene.community.views.register_hash', (), { "email": quote(email_address), 'emailHash': validationcode, } ),
                    'validationcode': validationcode,
                    'group': group,
                    })
            text_part = loader.get_template('sphene/community/accounts/account_verification_email.txt') \
                .render(mail_context)
            html_part = loader.get_template('sphene/community/accounts/account_verification_email.html') \
                .render(mail_context)

            msg = EmailMultiAlternatives(subject, text_part, None, [email_address])
            msg.attach_alternative(html_part, "text/html")
            msg.send()

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

class UserForm(forms.Form):
    username = forms.RegexField( username_re, label=ugettext_lazy(u'Username'))
    email_address = forms.CharField(label=ugettext_lazy(u'Email address'),
                                    widget = forms.TextInput(attrs={'disabled': 'disabled'}))
    email_hash = forms.CharField(widget=forms.HiddenInput)

    def clean_username(self):
        if User.objects.filter( username__exact = self.cleaned_data['username'] ).count() != 0:
            raise forms.ValidationError(ugettext(u'The username %(username)s is already taken.') % {'username': self.cleaned_data['username']})
        return self.cleaned_data['username']

    def clean_email_address(self):
        if User.objects.filter( email__exact = self.cleaned_data['email_address'] ).count() != 0:
            raise forms.ValidationError(ugettext(u'Another user is already registered with the email address %(email)s.')
                                        % {'email':self.cleaned_data['email_address']} )
        return self.cleaned_data['email_address']

class RegisterForm(UserForm):
    password = forms.CharField(label=ugettext_lazy(u'Password'),
                               widget = forms.PasswordInput )
    repassword = forms.CharField(label=ugettext_lazy(u'Verify Password'),
                                 widget = forms.PasswordInput )

    def clean(self):
        if not 'password' in self.cleaned_data or not 'repassword' in self.cleaned_data:
            return self.cleaned_data
        
        if self.cleaned_data['password'] != self.cleaned_data['repassword']:
            raise forms.ValidationError(ugettext(u'Passwords do not match.'))

        return self.cleaned_data



def register_hash(request, email, emailHash, group = None):
    email_address = unquote(email) #decryptString( settings.SECRET_KEY, emailHash )
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
        return render_to_response( 'sphene/community/register_hash.html',
                                   { 'form': form },
                                   context_instance = RequestContext(request) )
    
    elif md5(settings.SECRET_KEY + email_address).hexdigest() == emailHash:
        form = RegisterForm( )
        form.fields['email_address'].initial = email_address
        form.fields['email_hash'].initial = emailHash
        return render_to_response( 'sphene/community/register_hash.html',
                                   { 'form': form },
                                   context_instance = RequestContext(request) )
    else:
        print email_address
        print md5(settings.SECRET_KEY + email_address).hexdigest(), emailHash
        raise Http404("No Outstanding registrations for this user.")





##############################################################
####
#### The following code was copied from the django captchas project.
#### and slightly modified.

from django.http import HttpResponse
try:

    from djaptcha.models import CaptchaRequest
    from cStringIO import StringIO
    import random
    import Image,ImageDraw,ImageFont,ImageChops
    
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
    #image = Image.new('RGB', (40, 23), (39, 36, 81))
    # You need to specify the fonts dir and the font you are going to usue
    bgcolor = (39, 36, 81)
    if hasattr(settings,'CAPTCHA_BGCOLOR'):
        bgcolor = settings.CAPTCHA_BGCOLOR
    fgcolor = (153, 204, 0)
    if hasattr(settings,'CAPTCHA_FGCOLOR'):
        fgcolor = settings.CAPTCHA_FGCOLOR
    borderWidth = 2
    if hasattr(settings,'CAPTCHA_BORDER'):
        borderWidth = settings.CAPTCHA_BORDER
    font = ImageFont.truetype(settings.FONT_PATH,settings.FONT_SIZE)
    (width,height) = font.getsize(text)
    image = Image.new('RGB', (width+(borderWidth*2),height+(borderWidth*2)), bgcolor)
    draw = ImageDraw.Draw(image)
    # Draw the text, starting from (borderWidth,borderWidth) so the text won't be edge
    draw.text((borderWidth, borderWidth), text, font = font, fill = fgcolor)
    # Saves the image in a StringIO object, so you can write the response
    # in a HttpResponse object
    image = autocrop(image, bgcolor,borderWidth)
    out = StringIO()
    image.save(out,"JPEG")
    out.seek(0)
    response = HttpResponse()
    response['Content-Type'] = 'image/jpeg'
    response.write(out.read())
    return response

def autocrop(im, bgcolor, borderWidth = 0):
    if im.mode != 'RGB':
        im = im.convert('RGB')
    bg = Image.new('RGB', im.size, bgcolor)
    diff = ImageChops.difference(im, bg)
    bbox = diff.getbbox()
    if bbox:
        if borderWidth > 0:
            (x0,y0,x2,y2) = bbox

            if x0 > borderWidth:
                x0 = x0 - borderWidth
            else:
                x0 = 0

            if y0 > borderWidth:
                y0 = y0 - borderWidth
            else:
                y0 = 0

            if x2 + borderWidth < im.size[0]:
                x2 = x2 + borderWidth
            else:
                x2 = im.size[0]

            if y2 + borderWidth < im.size[1]:
                y2 = y2 + borderWidth
            else:
                y2 = im.size[1]

            bbox = (x0,y0,x2,y2)

        return im.crop(bbox)
    return im

def profile(request, group, user_id):
    user = get_object_or_404(User, pk = user_id)
    has_edit_permission = False
    profile_edit_url = None

    requester = request.user
    
    if user == requester or \
        (requester and requester.is_authenticated() and requester.is_superuser):
        has_edit_permission = True
        profile_edit_url = sph_reverse( 'sphene.community.views.profile_edit', (), { 'user_id': user.id, })

    ret = profile_display.send(None, request = request,
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
    requester = request.user
    
    if user_id:
        user = get_object_or_404(User, pk = user_id)
    else:
        user = requester

    if user is None or user != requester or not requester.is_authenticated():
        if not (requester and requester.is_authenticated() and (requester.is_superuser or has_permission_flag(requester, 'community_manage_users'))):
            raise PermissionDenied()

    if request.method == 'POST':
        reqdata = request.POST.copy()
        reqdata.update(request.FILES)
        form = EditProfileForm(user, request.POST, request.FILES)
    else:
        form = EditProfileForm(user)

    profile_edit_init_form.send(sender = EditProfileForm,
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

            profile_edit_save_form.send(sender = EditProfileForm,
                                        instance = form,
                                        request = request,
                                        )

            user.save()
            messages.success(request,  message = ugettext(u'Successfully changed user profile.') )
            
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
                               { 'profile_user': user,
                                 'form': form,
                                 'is_sphboard':'sphene.sphboard' in settings.INSTALLED_APPS
                                 },
                               context_instance = RequestContext(request) )



def admin_permission_rolegroup_list(request, group):
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
    if request.method == 'POST':
        name = request.POST['name']
        if name:
            RoleGroup(group = group,
                      name = name).save()
            return HttpResponseRedirect(sph_reverse('community_admin_permission_rolegroup_list'))
    rolegroups = RoleGroup.objects.filter( group = group )
    return render_to_response( 'sphene/community/admin/permission/rolegroup_list.html',
                               { 'rolegroups': rolegroups, },
                               context_instance = RequestContext(request) )

def admin_permission_rolegroup_edit(request, group, rolegroup_id):
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
    rolegroup = RoleGroup.objects.get( pk = rolegroup_id,
                                       group = group, )

    if request.method == 'POST':
        username = request.POST['username']
        if username:
            user = User.objects.get(username = username)
            RoleGroupMember(user = user,
                            rolegroup = rolegroup).save()
            return HttpResponseRedirect(rolegroup.get_absolute_editurl())

    if 'cmd' in request.GET and 'id' in request.GET:
        if request.GET['cmd'] == 'remove':
            member = rolegroup.rolegroupmember_set.get( pk = request.GET['id'] )
            messages.success(request,  
                message = ugettext( u'Removed user %(username)s from rolegroup.' ) % \
                    { 'username': member.user.username } )
            member.delete()
            return HttpResponseRedirect(rolegroup.get_absolute_editurl())


    return render_to_response( 'sphene/community/admin/permission/rolegroup_edit.html',
                               { 'rolegroup': rolegroup,
                                 },
                               context_instance = RequestContext(request) )

def admin_permission_role_list(request, group):
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
    roles = Role.objects.filter( group = group )
    return render_to_response( 'sphene/community/admin/permission/role_list.html',
                               { 'roles' : roles,
                                 },
                               context_instance = RequestContext(request) )

from forms import EditRoleForm

def admin_permission_role_edit(request, group, role_id = None):
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
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

            messages.success(request,  message = ugettext(u'Successfully saved role.') )
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
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
    role = get_object_or_404(Role, pk = role_id)
    members = role.rolemember_set.all()
    if 'cmd' in request.GET and request.GET['cmd'] == 'remove':
        memberid = request.GET['id']
        role_member = RoleMember.objects.get( pk = memberid )
        role_member.delete()

        messages.success(request,  message = ugettext(u'Successfully deleted role member.') )

        return HttpResponseRedirect( role.get_absolute_memberlisturl() )
    return render_to_response( 'sphene/community/admin/permission/role_member_list.html',
                               { 'members': members,
                                 'role': role,
                                 },
                               context_instance = RequestContext(request) )

from forms import EditRoleMemberForm, EditRoleGroupMemberForm

def admin_permission_role_member_add(request, group, role_id, addgroup = False):
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
    role = get_object_or_404(Role, pk = role_id)

    if addgroup:
        EditForm = EditRoleGroupMemberForm
    else:
        EditForm = EditRoleMemberForm

    if request.method == 'POST':
        form = EditForm(group = group, data = request.POST)
        if form.is_valid():
            data = form.cleaned_data
            role_member = RoleMember( role = role,
                                      user = data.get('user', None),
                                      rolegroup = data.get('rolegroup', None),
                                      has_limitations = data['has_limitations'], )
            role_member.save()
            if data['has_limitations']:
                limitation = RoleMemberLimitation( role_member = role_member,
                                                   object_type = data['object_type'],
                                                   object_id = data['object'], )
                limitation.save()
                
            messages.success(request,  message = ugettext(u'Successfully added member.') )
            return HttpResponseRedirect( role.get_absolute_memberlisturl() )
    else:
        form = EditForm(group = group)
    
    return render_to_response( 'sphene/community/admin/permission/role_member_add.html',
                               { 'form': form,
                                 'role': role,
                                 },
                               context_instance = RequestContext(request) )

def admin_permission_role_groupmember_add(request, group, role_id):
    if not has_permission_flag(request.user, 'community_manage_roles'):
        raise PermissionDenied()
    return admin_permission_role_member_add(request, group, role_id, True)

def admin_users(request, group):
    if not has_permission_flag(request.user, 'community_manage_users'):
        raise PermissionDenied()

    orderby = request.GET.get('orderby', 'username')

    users = User.objects.filter(is_superuser=False).order_by(orderby)
    search_qs = {}

    search_form = UsersSearchForm()
    if request.GET.has_key('search'):
        search_form = UsersSearchForm(request.GET)
        if search_form.is_valid():
            username = search_form.cleaned_data['username']
            if username:
                search_params = Q(username__istartswith=username)|Q(first_name__istartswith=username)|Q(last_name__istartswith=username)
                users = users.filter(search_params)
                search_qs = urllib.urlencode(search_form.cleaned_data)
    
    templateName = 'sphene/community/admin/users_list.html'

    context = {'is_sphboard':'sphene.sphboard' in settings.INSTALLED_APPS,
               'search_qs':search_qs,
               'search_form':search_form,
               'orderby':orderby}

    res =  object_list( request = request,
                        queryset = users,
                        template_name = templateName,
                        template_object_name = 'sphuser',
                        allow_empty = True,
                        extra_context = context,
                        paginate_by = 10,
                        )

    return res

def admin_user_switch_active(request, user_id, group):
    if not has_permission_flag(request.user, 'community_manage_users'):
        raise PermissionDenied()
    usr = get_object_or_404(User, pk=user_id, is_superuser=False)
    usr.is_active = not usr.is_active
    usr.save()

    user_status = _('no')
    button_label = _('Enable')
    if usr.is_active:
        user_status=_('yes')
        button_label = _('Disable')

    if not request.is_ajax():
        messages.success(request,  message = ugettext(u'Successfully changed user status.') )
        url = request.REQUEST.get('next', reverse('sph_admin_users'))
        return HttpResponseRedirect(url)
    else:
        return HttpResponse(simplejson.dumps({"user_status":user_status,
                                              "button_label":button_label}),
                            mimetype='application/json')


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
    if 'content_type_id' not in request.GET or \
            not request.GET.get( 'string', '' ):
        raise Http404
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
        params = [ content_type_id ], ).distinct()[:10]
    ret = ''
    for taglabel in taglabels:
        ret += '<taglabel><id>%d</id><label>%s</label><tag>%s</tag></taglabel>' % ( taglabel.id,
                                                                                    taglabel.label,
                                                                                    taglabel.tag.name )

    return HttpResponse("<taglabels>%s</taglabels>" % ret,
                        mimetype = 'text/xml', )



class RevealEmailAddress(forms.Form):
    captcha = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
                                    help_text = ugettext('Please enter the result of the above calculation.'),
                                    )
    


def reveal_emailaddress(request, group, user_id):
    if request.method == 'POST':
        form = RevealEmailAddress(request.POST)
        if form.is_valid():
            request.session['sph_email_captcha_validated'] = time()
            user = User.objects.get( pk = user_id )
            return HttpResponseRedirect( sph_user_profile_link( user ) )
    else:
        form = RevealEmailAddress()
    return render_to_response( 'sphene/community/profile_reveal_emailaddress.html',
                               { 'form': form,
                                 },
                               context_instance = RequestContext(request) )

