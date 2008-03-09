from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from sphene.community.sphpermalink import sphpermalink as permalink, get_urlconf
from django.utils.translation import ugettext as _
from django.db import connection
import logging
import re

logger = logging.getLogger('sphene.community.models')

# Create your models here.

class Group(models.Model):
    name = models.CharField(max_length = 250)
    longname = models.CharField(max_length = 250)
    default_theme = models.ForeignKey('Theme', null = True, blank = True)
    parent = models.ForeignKey('Group', null = True, blank = True)
    baseurl = models.CharField(max_length = 250)

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

    def __unicode__(self):
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
        name = models.CharField(max_length = 250)
        path = models.CharField(max_length = 250)

        def __unicode__(self):
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
        label = models.CharField(max_length = 250)
        href  = models.CharField(max_length = 250)
        urltype = models.IntegerField( default = 0, choices = NAVIGATION_URL_TYPES )
        sortorder = models.IntegerField( default = 100 )
        navigationType = models.IntegerField( default = 0, choices = NAVIGATION_TYPES )


        def __unicode__(self):
                return self.label

        class Meta:
                ordering = ['sortorder']

        class Admin:
                list_display = ( 'label', 'group', 'href', 'navigationType', 'sortorder' )
                list_filter = ( 'group', 'navigationType' )
                ordering = ['group', 'navigationType', 'sortorder']
        

class ApplicationChangelog(models.Model):
        app_label = models.CharField(max_length = 250)
        model = models.CharField(max_length = 250)
        version = models.CharField(max_length = 250)
        applied = models.DateTimeField()

        class Meta:
                get_latest_by = 'applied'


from sphene.community.sphsettings import get_sph_setting
#from sphene.community import sphutils

class CommunityUserProfile(models.Model):
    user = models.ForeignKey( User, unique = True)
    public_emailaddress = models.CharField(max_length = 250)

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
    name = models.CharField(max_length = 250)
    help_text = models.CharField(max_length = 250, blank = True, help_text = 'An optional help text displayed to the user.' )
    regex = models.CharField(max_length = 250, blank = True, help_text = 'An optional regular expression to validate user input.', )
    renderstring = models.CharField(max_length = 250, blank = True, help_text = 'An optional render string how the value should be displayed in the profile (e.g. &lt;a href="%(value)s"&gt;%(value)s&lt;/a&gt; - default: %(value)s' )
    sortorder = models.IntegerField()

    class Meta:
        ordering = [ 'sortorder' ]

    class Admin:
        list_display = ('name', 'regex', 'renderstring', 'sortorder', )

class CommunityUserProfileFieldValue(models.Model):
    user_profile = models.ForeignKey( CommunityUserProfile )
    profile_field = models.ForeignKey( CommunityUserProfileField )

    value = models.CharField( max_length = 250 )

    class Meta:
        unique_together = (("user_profile", "profile_field"),)

class GroupTemplate(models.Model):
    """
    Represents a group specific template which can be used to overload
    any django template from the filesystem.
    """
    group = models.ForeignKey(Group)
    template_name = models.CharField( max_length = 250, db_index = True )
    source = models.TextField()

    def __unicode__(self):
        return self.template_name
    
    class Meta:
        unique_together = (("group", "template_name"),)

    class Admin:
        list_display = ('template_name', 'group')
        list_filter = ( 'group', 'template_name' )


class PermissionFlag(models.Model):
    """
    Permission flags are predefined (in the code) flags of user rights.
    Very similar to django's permissions.

    (I decided against using django's permissions for the sake of simplicity..
    i don't like the idea of auto generating permissions which aren't used
    in the application code (but only within the django administration))
    """
    name = models.CharField( max_length = 250, unique = True )


    sph_permission_flags = { 'group_administrator':
                             'Users with this permission flag have all permissions.',

                             'community_manage_roles':
                             'User have permission to create, edit and assign roles.',
                             }


    def __unicode__(self):
        return self.name

class Role(models.Model):
    """
    A role is a user defined collection of so called permission flags.
    """
    name = models.CharField( max_length = 250 )
    group = models.ForeignKey( Group )

    permission_flags = models.ManyToManyField( PermissionFlag, related_name = 'roles' )


    def get_permission_flag_string(self):
        return ", ".join( [flag.name for flag in self.permission_flags.all()] )

    def __unicode__(self):
        return '%s - %s' % (self.group.name, self.name)

    def get_absolute_editurl(self):
        return ('sphene.community.views.admin_permission_role_edit', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_editurl = permalink(get_absolute_editurl, get_urlconf)

    def get_absolute_memberlisturl(self):
        return ('sphene.community.views.admin_permission_role_member_list', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_memberlisturl = permalink(get_absolute_memberlisturl, get_urlconf)

    def get_absolute_memberaddurl(self):
        return ('sphene.community.views.admin_permission_role_member_add', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_memberaddurl = permalink(get_absolute_memberaddurl, get_urlconf)

    class Meta:
        unique_together = (('name', 'group'),)

    class Admin:
        ordering = ('group', 'name')


class RoleMember(models.Model):
    """
    A role member is the relation between a given role and a user.
    This relation might has additional limitations - e.g. for the board
    it might only be active within one given category -
    see RoleMemberLimitation.

    If there are no limitations (has_limitations = False) then the role
    is active for the user globally within the role's group.
    """
    role = models.ForeignKey( Role )
    user = models.ForeignKey( User )

    has_limitations = models.BooleanField()


    def get_limitations_string(self):
        if not self.has_limitations:
            return "None"
        limitation = self.rolememberlimitation_set.get()
        return "%s: %s" % (limitation.object_type.model_class()._meta.object_name, unicode(limitation.content_object))

    class Admin:
        pass


class RoleMemberLimitation(models.Model):
    """
    Limits the membership of a user to a role by only applying to a
    specific object.
    """
    role_member = models.ForeignKey( RoleMember )

    object_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index = True)

    content_object = generic.GenericForeignKey(ct_field = 'object_type')

    class Meta:
        unique_together = (('role_member', 'object_type', 'object_id'),)



#########################################################
###
### tagging
###
### Tagging is in part inspired by django-tagging: 
###    http://code.google.com/p/django-tagging/
### (but because of various reasons - e.g. that i want tags separated by group - 
###  i decided to implement tagging from scratch)

tag_sanitize_regex = re.compile(r'[^\w]+', re.S | re.U)

def tag_sanitize(tag_label):
    return tag_sanitize_regex.sub('', tag_label).lower()

def tag_set_labels(model_instance, tag_labels):
    """
    sets the tags of the given model_instance (which must exists already!)
    to the given tag labels (which must be TagLabel models.)
    - removes all existing tags.
    """

    # First remove existing tag labels
    model_type = ContentType.objects.get_for_model(model_instance)
    TaggedItem.objects.filter( content_type__pk = model_type.id,
                               object_id = model_instance.id, ).delete()

    for tag_label in tag_labels:
        t = TaggedItem( object = model_instance,
                        tag_label = tag_label )
        t.save()


def tag_get_labels(model_instance):
    """
    returns all TagLabel objects for the given model_instance.
    """
    model_type = ContentType.objects.get_for_model(model_instance)
    tagged_items = TaggedItem.objects.filter( content_type__pk = model_type.id,
                                              object_id = model_instance.id, )

    tag_labels = list()
    for tagged_item in tagged_items:
        tag_labels.append( tagged_item.tag_label )

    return tag_labels

qn = connection.ops.quote_name

def get_queryset_and_model(queryset_or_model):
    try:
        return queryset_or_model, queryset_or_model.model
    except AttributeError:
        return queryset_or_model._default_manager.all(), queryset_or_model

def tag_get_models_by_tag(queryset_or_model, tag):
    # pretty much copied from django-tagging
    queryset, model = get_queryset_and_model(queryset_or_model)
    content_type = ContentType.objects.get_for_model(model)
    opts = TaggedItem._meta
    tagged_item_table = qn(opts.db_table)
    tag_label_table = qn(TagLabel._meta.db_table)
    return queryset.extra(
        tables=[TaggedItem._meta.db_table,
               TagLabel._meta.db_table, ],
        where=[
            '%s.content_type_id = %%s' % tagged_item_table,
            '%s.tag_id = %%s' % tag_label_table,
            '%s.tag_label_id = %s.%s' % (tagged_item_table,
                                         tag_label_table,
                                         TagLabel._meta.pk.column),
            '%s.%s = %s.object_id' % (qn(model._meta.db_table),
                                      qn(model._meta.pk.column),
                                      tagged_item_table)
            ],
        params=[content_type.pk, tag.pk],
        )

class Tag(models.Model):
    """
    A tag is the internal representation which is always linked to a specific group.

    A tag name only allows alpha numeric characters without spaces, etc. and only stores
    lower case letters !
    """
    group = models.ForeignKey( Group )
    name = models.CharField( max_length = 250, )

    def __unicode__(self):
        return self.name

    class Meta:
        unique_together = (("group", "name"))

class TagLabel(models.Model):
    """
    A tag label represents the user entered value for the tag. Including uppercase/lowercase,
    and all characters usually not allowed within a tag.
    """
    tag = models.ForeignKey(Tag, related_name = 'labels')
    label = models.CharField( max_length = 250, )

    def __unicode__(self):
        return self.label

    class Meta:
        unique_together = (("tag", "label"))

class TaggedItem(models.Model):
    """
    Relationship between a tag label and an item.
    """
    tag_label = models.ForeignKey(TagLabel, related_name = 'items')
    content_type = models.ForeignKey(ContentType, related_name = 'sph_taggeditem_set')
    object_id = models.PositiveIntegerField(db_index=True)
    object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = (('tag_label', 'content_type', 'object_id'))

#########################################################
###
### hooks
###

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
        
    instance.fields['community_settings'] = Separator(label=_(u'Community settings'))
    instance.fields['public_emailaddress'] = forms.CharField( label = _(u'Public email address'),
                                                              required = False,
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
    
    request.user.message_set.create( message = _("Successfully saved community profile.") )

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


