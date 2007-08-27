from django.db import models
from django.contrib.auth.models import User
import logging

logger = logging.getLogger('sphene.community.models')

# Create your models here.

class Group(models.Model):
    name = models.CharField(maxlength = 250)
    longname = models.CharField(maxlength = 250)
    default_theme = models.ForeignKey('Theme', null = True, blank = True)
    parent = models.ForeignKey('Group', null = True, blank = True)
    baseurl = models.CharField(maxlength = 250)

    def get_name(self):
        return self.longname or self.name

    def recursiveName(self):
        recname = ''
        if self.parent:
            recname = self.parent.recursiveName() + ' / '
        return recname + self.name

    def get_member(self, user):
        try:
            return GroupMember.objects.get( group = self,
                                            user = user, )
        except GroupMember.DoesNotExist:
            return None

    def __str__(self):
        return self.name;

    class Admin:
        pass

class GroupMember(models.Model):
        group = models.ForeignKey( Group, edit_inline = models.TABULAR, core = True )
        user = models.ForeignKey( User, core = True, )

        class Admin:
                list_display = ('group', 'user',)
                list_filter = ('group',)

class Theme(models.Model):
        name = models.CharField(maxlength = 250)
        path = models.CharField(maxlength = 250)

        def __str__(self):
                return self.name;

        class Admin:
                pass

NAVIGATION_URL_TYPES = (
        (0, 'Relative (e.g. /wiki/show/Start)'),
        (1, 'Absolute (e.g. http://sphene.net')
        )

NAVIGATION_TYPES = (
        (0, 'Left Main Navigation'),
        (1, 'Top navigation')
        )

class Navigation(models.Model):
        group = models.ForeignKey(Group)
        label = models.CharField(maxlength = 250)
        href  = models.CharField(maxlength = 250)
        urltype = models.IntegerField( default = 0, choices = NAVIGATION_URL_TYPES )
        sortorder = models.IntegerField( default = 100 )
        navigationType = models.IntegerField( default = 0, choices = NAVIGATION_TYPES )


        def __str__(self):
                return self.label

        class Meta:
                ordering = ['sortorder']

        class Admin:
                list_display = ( 'label', 'group', 'href', 'navigationType' )
                list_filter = ( 'group', 'navigationType' )
                ordering = ['group', 'navigationType', 'sortorder']
        

class ApplicationChangelog(models.Model):
        app_label = models.CharField(maxlength = 250)
        model = models.CharField(maxlength = 250)
        version = models.CharField(maxlength = 250)
        applied = models.DateTimeField()

        class Meta:
                get_latest_by = 'applied'


from sphene.community.sphsettings import get_sph_setting
#from sphene.community import sphutils

class CommunityUserProfile(models.Model):
    user = models.ForeignKey( User, unique = True)
    public_emailaddress = models.CharField(maxlength = 250)

    avatar = models.ImageField( height_field = 'avatar_height',
                                width_field = 'avatar_width',
                                upload_to = get_sph_setting('community_avatar_upload_to'),
                                blank = True, null = True, )
    avatar_height = models.IntegerField(blank = True, null = True, )
    avatar_width = models.IntegerField(blank = True, null = True, )


    changelog = ( ( '2007-08-10 00', 'alter', 'ADD avatar varchar(100)'   ),
                  ( '2007-08-10 01', 'alter', 'ADD avatar_height integer' ),
                  ( '2007-08-10 02', 'alter', 'ADD avatar_width integer'  ) )

class CommunityUserProfileField(models.Model):
    """ User profile fields, configurable through the django admin
    interface. """
    name = models.CharField(maxlength = 250)
    help_text = models.CharField(maxlength = 250, blank = True, help_text = 'An optional help text displayed to the user.' )
    regex = models.CharField(maxlength = 250, blank = True, help_text = 'An optional regular expression to validate user input.', )
    renderstring = models.CharField(maxlength = 250, blank = True, help_text = 'An optional render string how the value should be displayed in the profile (e.g. &lt;a href="%(value)s"&gt;%(value)s&lt;/a&gt; - default: %(value)s' )
    sortorder = models.IntegerField()

    class Meta:
        ordering = [ 'sortorder' ]

    class Admin:
        list_display = ('name', 'regex', 'renderstring', 'sortorder', )

class CommunityUserProfileFieldValue(models.Model):
    user_profile = models.ForeignKey( CommunityUserProfile )
    profile_field = models.ForeignKey( CommunityUserProfileField )

    value = models.CharField( maxlength = 250 )

    class Meta:
        unique_together = (("user_profile", "profile_field"),)

class GroupTemplate(models.Model):
    group = models.ForeignKey(Group)
    template_name = models.CharField( maxlength = 250, db_index = True )
    source = models.TextField()
    
    class Meta:
        unique_together = (("group", "template_name"),)

    class Admin:
        pass


from django.dispatch import dispatcher
from django import newforms as forms
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display



def community_profile_edit_init_form(sender, instance, signal, request, *args, **kwargs):
    user = instance.user
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        profile = CommunityUserProfile( user = user, )
        
    instance.fields['community_settings'] = Separator()
    instance.fields['public_emailaddress'] = forms.CharField( required = False,
                                                              initial = profile.public_emailaddress )

    fields = CommunityUserProfileField.objects.all()
    for field in fields:
        initial = ''
        if profile.id:
            try:
                value = CommunityUserProfileFieldValue.objects.get( user_profile = profile,
                                                                    profile_field = field, )
                initial = value.value
            except CommunityUserProfileFieldValue.DoesNotExist:
                pass
                                                    
        instance.fields['community_field_%d' % field.id] = forms.RegexField( regex = field.regex,
                                                                             label = field.name,
                                                                             help_text = field.help_text,
                                                                             initial = initial,
                                                                             required = False,
                                                                             )

def community_profile_edit_save_form(sender, instance, signal, request, *args, **kwargs):
    data = instance.cleaned_data
    user = instance.user
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        profile = CommunityUserProfile( user = user, )

    profile.public_emailaddress = data['public_emailaddress']
    profile.save()

    fields = CommunityUserProfileField.objects.all()
    for field in fields:
        try:
            value = CommunityUserProfileFieldValue.objects.get( user_profile = profile,
                                                                profile_field = field, )
            initial = value.value
        except CommunityUserProfileFieldValue.DoesNotExist:
            value = CommunityUserProfileFieldValue( user_profile = profile,
                                                    profile_field = field, )
        newvalue = data['community_field_%d' % field.id]
        if newvalue:
            value.value = data['community_field_%d' % field.id]
            value.save()
        else:
            if value.id: value.delete()
    
    request.user.message_set.create( message = "Successfully saved community profile." )

def community_profile_display(sender, signal, request, user):
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        return None

    ret = ''
    fields = CommunityUserProfileField.objects.all()
    for field in fields:
        try:
            value = CommunityUserProfileFieldValue.objects.get( user_profile = profile,
                                                                profile_field = field, )
            formatstring = '<tr><th>%(label)s</th><td>' + (field.renderstring or '%(value)s') + '</td></tr>'
            ret += (formatstring % { 'label': field.name,
                                     'value': value.value, })
        except CommunityUserProfileFieldValue.DoesNotExist:
            continue
                                            
    return ret

dispatcher.connect(community_profile_edit_init_form, signal = profile_edit_init_form, sender = EditProfileForm)
dispatcher.connect(community_profile_edit_save_form, signal = profile_edit_save_form, sender = EditProfileForm)
dispatcher.connect(community_profile_display, signal = profile_display)


