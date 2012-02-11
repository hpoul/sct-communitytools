from django import forms
from django.utils.translation import ugettext_lazy as _, ugettext

from sphene.community.signals import profile_edit_init_form

class Separator(forms.Field):
    def __init__(self, *args, **kwargs):
        super(Separator, self).__init__( required = False, *args, **kwargs)

    def is_separator(self):
        return True

class EditProfileForm(forms.Form):
    first_name = forms.CharField(label=_(u'First name'), required=False)
    last_name = forms.CharField(label=_(u'Last name'), required=False)
    email_address = forms.CharField(label=_(u'Email address'))

    change_password = Separator(label=_(u'Change password'),
                                help_text = _(u'To modify your password fill out the following three fields.') )
    current_password = forms.CharField(widget = forms.PasswordInput(),
                                       label=_(u'Current password'),
                                       required = False)
    new_password = forms.CharField(widget = forms.PasswordInput(),
                                   label=_(u'New password'),
                                   required = False )
    repassword = forms.CharField( widget = forms.PasswordInput(),
                                  label = _(u'Retype your new password'),
                                  required = False )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(EditProfileForm, self).__init__( *args, **kwargs )


    def clean_current_password(self):
        current_password = self.cleaned_data['current_password']
        if current_password and \
           not self.user.check_password(current_password):
            raise forms.ValidationError(_(u'Invalid password.'))
        return self.cleaned_data

    def clean_repassword(self):
        password = self.cleaned_data['new_password']
        repassword = self.cleaned_data['repassword']
        if not password == repassword:
            raise forms.ValidationError(_(u'Passwords do not match.'))
        return self.cleaned_data


from django.contrib.auth.models import User
from django.db.models import signals, get_apps, get_models
from django.contrib.contenttypes.models import ContentType

def get_object_type_choices():
    ret = list()
    ret.append( ('', _(u'-- Select Object Type --')) )
    apps = get_apps()
    for app in apps:
        ms = get_models(app)
        for m in ms:
            if hasattr(m.objects, 'rolemember_limitation_objects'):
                ret.append( (ContentType.objects.get_for_model(m).id, m._meta.object_name) )

    return ret


def get_object_id_choices(object_type, group):
    ret = list()
    m = object_type.model_class()
    objs = m.objects.rolemember_limitation_objects(group)
    for obj in objs:
        ret.append( (obj.id, unicode(obj)) )
    return ret

def get_permission_flag_choices():
    ret = list()

    apps = get_apps()
    for app in apps:
        ms = get_models(app)
        for klass in ms:
            if hasattr(klass, 'sph_permission_flags'):
                sph_permission_flags = klass.sph_permission_flags

                if isinstance(sph_permission_flags, dict):
                    sph_permission_flags = sph_permission_flags.iteritems()

                for (flag, description) in sph_permission_flags:
                    ret.append( (flag, "%s (%s)" % (flag, unicode(description)) ) )

    return ret

class EditRoleForm(forms.Form):
    name = forms.CharField(label=_(u'Name'))
    permission_flags = forms.MultipleChoiceField(label=_(u'Permission flags'))

    def __init__(self, *args, **kwargs):
        super(EditRoleForm, self).__init__( *args, **kwargs )
        self.fields['permission_flags'].choices = get_permission_flag_choices()


autosubmit_args = { 'onchange': 'this.form.auto_submit.value = "on";this.form.submit();' }

class BasicRoleMemberForm(forms.Form):
#    username = forms.CharField()
    has_limitations = forms.BooleanField( label=_(u'Has limitations'), widget = forms.CheckboxInput( attrs = autosubmit_args ), required = False, help_text = _(u'Allows you to limit the given permission to only one specific object.') )
    auto_submit = forms.BooleanField(widget = forms.HiddenInput, required = False)

    def __init__(self, group, *args, **kwargs):
        super(BasicRoleMemberForm, self).__init__( *args, **kwargs )
        if self.data.get( 'has_limitations', False ):
            self.fields['object_type'] = forms.ChoiceField(label=ugettext(u'Object type'), choices = get_object_type_choices(), widget = forms.Select( attrs = autosubmit_args ) )

        if self.data.get( 'object_type', ''):
            object_type = ContentType.objects.get( pk = self.data['object_type'] )
            self.fields['object'] = forms.ChoiceField(label=ugettext(u'Object'), choices = get_object_id_choices(object_type, group) )

    def clean_object_type(self):
        try:
            return ContentType.objects.get( pk = self.cleaned_data['object_type'] )
        except ContentType.DoesNotExist:
            raise forms.ValidationError(_(u'Invalid Object Type'))

class UsernameRoleMemberForm(forms.Form):
    username = forms.CharField(label=_(u'Username'))

    def clean_username(self):
        try:
            user = User.objects.get( username = self.cleaned_data['username'] )
            self.cleaned_data['user'] = user
        except User.DoesNotExist:
            raise forms.ValidationError(_(u'User does not exist.'))
        return self.cleaned_data['username']


#class RoleGroupChoiceField(forms.ModelChoiceField):
#    def label_from_instance(self, obj):
#        return obj.name

class RoleGroupMemberForm(forms.Form):
    rolegroup = forms.ModelChoiceField(queryset=None, label=_(u'Role group'))

    def __init__(self, group, *args, **kwargs):
        super(RoleGroupMemberForm, self).__init__( group = group, *args, **kwargs )

        from sphene.community.models import RoleGroup
        self.fields['rolegroup'].queryset = RoleGroup.objects.filter( group = group )

class EditRoleMemberForm(UsernameRoleMemberForm, BasicRoleMemberForm):
    pass


class EditRoleGroupMemberForm(RoleGroupMemberForm, BasicRoleMemberForm):
    pass

class UsersSearchForm(forms.Form):
    username = forms.CharField(label=_(u'Username'), required=False)
