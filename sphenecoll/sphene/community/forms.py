from django import newforms as forms
from django.dispatch import dispatcher

from sphene.community.signals import profile_edit_init_form


class Separator(forms.Field):
    def __init__(self, *args, **kwargs):
        super(Separator, self).__init__( required = False, *args, **kwargs)
    
    def is_separator(self):
        return True

class EditProfileForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email_address = forms.CharField()

    change_password = Separator( help_text = 'To modify your password fill out the following three fields.' )
    current_password = forms.CharField( widget = forms.PasswordInput(), required = False )
    new_password = forms.CharField( widget = forms.PasswordInput(), required = False )
    repassword = forms.CharField( widget = forms.PasswordInput(),
                                  label = "Retype your new password",
                                  required = False )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(EditProfileForm, self).__init__( *args, **kwargs )


    def clean_current_password(self):
        current_password = self.cleaned_data['current_password']
        if current_password and \
           not self.user.check_password(current_password):
            raise forms.ValidationError("Invalid password.")
        return self.cleaned_data

    def clean_repassword(self):
        password = self.cleaned_data['new_password']
        repassword = self.cleaned_data['repassword']
        if not password == repassword:
            raise forms.ValidationError("Passwords do not match.")
        return self.cleaned_data
    
