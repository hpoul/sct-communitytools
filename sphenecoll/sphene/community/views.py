# Create your views here.


from django import newforms as forms
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.template import loader, Context
from django.core.mail import send_mail
from django.contrib.auth import authenticate,login

from sphene.contrib.libs.common.utils.misc import cryptString, decryptString

class RegisterEmailAddress(forms.Form):
    email_address = forms.EmailField()
    
    def clean(self):
        if 'email_address' not in self.cleaned_data:
            return self.cleaned_data

        if User.objects.filter( email__exact = self.cleaned_data['email_address'] ).count() != 0:
            raise forms.ValidationError("Another user is already registered with the email address %s."
                                        % self.cleaned_data['email_address'] )
        return self.cleaned_data


def register(request, group = None):

    if request.method == 'POST':
        form = RegisterEmailAddress(request.POST)
        if form.is_valid():
            regdata = form.cleaned_data
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
        if self.cleaned_data['password'] != self.cleaned_data['repassword']:
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter( username__exact = self.cleaned_data['username'] ).count() != 0:
            raise forms.ValidationError("The username %s is already taken." % self.cleaned_data['username'])
        if User.objects.filter( email__exact = self.cleaned_data['email_address'] ).count() != 0:
            raise forms.ValidationError("Another user is already registered with the email address %s."
                                        % self.cleaned_data['email_address'] )
        return self.cleaned_data


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
