# Create your views here.


from django import newforms as forms
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template import loader, Context
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login

from utils.misc import cryptString, decryptString

class RegisterEmailAddress(forms.Form):
    email_address = forms.EmailField()


def register(request, group = None):

    if request.method == 'POST':
        form = RegisterEmailAddress(request.POST)
        if form.is_valid():
            regdata = form.clean_data
            email_address = regdata['email_address']
            if group:
                subject = 'Email verification required'
            else:
                subject = 'Email verification required for site %s' % group.get_name()
            validationcode = cryptString( settings.SECRET_KEY, email_address )
            t = loader.get_template('sphene/community/accounts/account_verification_email.txt')
            c = {
                'email': email_address,
                'baseurl': group.baseurl,
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
    username = forms.RegexField( username_re )
    email_address = forms.CharField( widget = forms.TextInput( attrs = { 'disabled': 'disabled' } ) )
    password = forms.CharField( widget = forms.PasswordInput )
    repassword = forms.CharField( label = 'Verify Password', widget = forms.PasswordInput )

    def clean(self):
        if self.clean_data['password'] != self.clean_data['repassword']:
            raise forms.ValidationError("Passwords do not match.")
        return self.clean_data


def register_hash(request, emailHash, group = None):
    email_address = decryptString( settings.SECRET_KEY, emailHash )
    if request.method == 'POST':
        post = request.POST.copy()
        post.update( { 'email_address': email_address } )
        form = RegisterForm( post )
        if form.is_valid():
            formdata = form.clean_data
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

