from django.db import models
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext as _, ugettext_lazy
from django.db import connection
from django.db.models.signals import post_save, m2m_changed, post_delete

from sphene.community.sphpermalink import sphpermalink
from sphene.community.signals import clear_user_displayname, clear_permissions_cache_rgm, clear_permissions_cache_rml, \
                                     clear_permissions_cache_rm, clear_permission_flag_cache

import logging
import re


logger = logging.getLogger('sphene.community.models')
# Create your models here.

class Group(models.Model):
    name = models.CharField(max_length = 250)
    longname = models.CharField(max_length = 250)
    default_theme = models.ForeignKey('Theme', null = True, blank = True)
    parent = models.ForeignKey('Group', null = True, blank = True)
    baseurl = models.CharField(max_length = 250, help_text = 'The base URL under which this group will be available. Example: sct.sphene.net')

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

    def get_baseurl(self):
        """
        Returns the "base URL" including http:// and without tailing slash.
        """
        url = self.baseurl
        if not (url.startswith('http://') or url.startswith('https://')):
            url = 'http://%s' % url
        if url.endswith('/'):
            url = url[0:-1]
        return url

    def __unicode__(self):
        return self.get_name();

    class Meta:
        verbose_name = ugettext_lazy('Group')
        verbose_name_plural = ugettext_lazy('Groups')

USERLEVEL_CHOICES = (
    (0, ugettext_lazy('Normal User')),
    (5, ugettext_lazy('Administrator')),
    )

class GroupMember(models.Model):
        group = models.ForeignKey(Group, verbose_name=ugettext_lazy(u'Group'))
        user = models.ForeignKey( User, verbose_name=ugettext_lazy(u'User'))
        userlevel = models.IntegerField( choices = USERLEVEL_CHOICES )


        changelog = ( ( '2008-04-06 00', 'alter', 'ADD userlevel integer', ),
                      ( '2008-04-06 01', 'update', 'SET userlevel = 0', ),
                      ( '2008-04-06 02', 'alter', 'ALTER userlevel SET NOT NULL', ), )


        def get_userlevel_str(self):
            for value, str in USERLEVEL_CHOICES:
                if value == self.userlevel:
                    return str;

        class Meta:
            verbose_name = ugettext_lazy('Group member')
            verbose_name_plural = ugettext_lazy('Group members')


class Theme(models.Model):
        name = models.CharField(max_length = 250)
        path = models.CharField(max_length = 250)

        def __unicode__(self):
                return self.name;

        class Meta:
            verbose_name = ugettext_lazy('Theme')
            verbose_name_plural = ugettext_lazy('Themes')

NAVIGATION_URL_TYPES = (
        (0, 'Relative (e.g. /wiki/show/Start)'),
        (1, 'Absolute (e.g. http://sphene.net')
        )

NAVIGATION_TYPES = (
        (0, 'Left Main Navigation'),
        (1, 'Top navigation')
        )

class Navigation(models.Model):
        group = models.ForeignKey(Group, verbose_name=ugettext_lazy(u'Group'))
        label = models.CharField(max_length = 250)
        href  = models.CharField(max_length = 250)
        urltype = models.IntegerField( default = 0, choices = NAVIGATION_URL_TYPES )
        sortorder = models.IntegerField( default = 100 )
        navigationType = models.IntegerField( default = 0, choices = NAVIGATION_TYPES )


        def __unicode__(self):
            return self.label

        def is_active(self):
            from sphene.community.middleware import get_current_request
            req = get_current_request()
            if not req:
                return False
            nav = getattr(req, 'nav', req.path)
            if self.href == '/':
                return self.href == nav or nav == ''
            return nav.startswith(self.href)

        class Meta:
                verbose_name = ugettext_lazy('Navigation')
                verbose_name_plural = ugettext_lazy('Navigations')
                ordering = ['sortorder']
        

class ApplicationChangelog(models.Model):
        app_label = models.CharField(max_length = 250)
        model = models.CharField(max_length = 250)
        version = models.CharField(max_length = 250)
        applied = models.DateTimeField()

        class Meta:
                verbose_name = ugettext_lazy('Application change log')
                verbose_name_plural = ugettext_lazy('Application change logs')
                get_latest_by = 'applied'


from sphene.community.sphsettings import get_sph_setting
#from sphene.community import sphutils

class CommunityUserProfile(models.Model):
    user = models.ForeignKey( User, unique = True, verbose_name=ugettext_lazy(u'User'))
    displayname = models.CharField(ugettext_lazy(u'Display name'), max_length = 250)
    public_emailaddress = models.CharField(ugettext_lazy(u'Public email address'), max_length = 250)
    
    avatar = models.ImageField( ugettext_lazy(u'Avatar'),
                                height_field = 'avatar_height',
                                width_field = 'avatar_width',
                                upload_to = get_sph_setting('community_avatar_upload_to'),
                                blank = True, null = True, )
    avatar_height = models.IntegerField(ugettext_lazy(u'Avatar height'), blank = True, null = True, )
    avatar_width = models.IntegerField(ugettext_lazy(u'Avatar width'), blank = True, null = True, )


    changelog = ( ( '2007-08-10 00', 'alter', 'ADD avatar varchar(100)'   ),
                  ( '2007-08-10 01', 'alter', 'ADD avatar_height integer' ),
                  ( '2007-08-10 02', 'alter', 'ADD avatar_width integer'  ),
                  ( '2008-04-10 00', 'alter', 'ADD displayname varchar(250)' ),
                  ( '2008-04-10 01', 'update', "SET displayname = ''" ),
                  ( '2008-04-10 02', 'alter', 'ALTER displayname SET NOT NULL' ),
                )

    class Meta:
        verbose_name = ugettext_lazy('Community user profile')
        verbose_name_plural = ugettext_lazy('Community user profiles')

class CommunityUserProfileField(models.Model):
    """ User profile fields, configurable through the django admin
    interface. """
    name = models.CharField(max_length = 250)
    help_text = models.CharField(max_length = 250, blank = True, help_text = 'An optional help text displayed to the user.' )
    regex = models.CharField(max_length = 250, blank = True, help_text = 'An optional regular expression to validate user input.', )
    renderstring = models.CharField(max_length = 250, blank = True, help_text = 'An optional render string how the value should be displayed in the profile (e.g. &lt;a href="%(value)s"&gt;%(value)s&lt;/a&gt; - default: %(value)s' )
    sortorder = models.IntegerField()

    class Meta:
        verbose_name = ugettext_lazy('Community user profile field')
        verbose_name_plural = ugettext_lazy('Community user profile fields')
        ordering = [ 'sortorder' ]


class CommunityUserProfileFieldValue(models.Model):
    user_profile = models.ForeignKey( CommunityUserProfile, verbose_name=ugettext_lazy(u'User profile'))
    profile_field = models.ForeignKey( CommunityUserProfileField, verbose_name=ugettext_lazy(u'Profile field') )

    value = models.CharField( max_length = 250 )

    class Meta:
        verbose_name = ugettext_lazy('Community user profile field value')
        verbose_name_plural = ugettext_lazy('Community user profile field values')
        unique_together = (("user_profile", "profile_field"),)


class GroupTemplate(models.Model):
    """
    Represents a group specific template which can be used to overload
    any django template from the filesystem.
    """
    group = models.ForeignKey(Group, verbose_name=ugettext_lazy(u'Group'))
    template_name = models.CharField( max_length = 250, db_index = True )
    source = models.TextField()

    def __unicode__(self):
        return self.template_name
    
    class Meta:
        verbose_name = ugettext_lazy('Group template')
        verbose_name_plural = ugettext_lazy('Group templates')
        unique_together = (("group", "template_name"),)


class PermissionFlag(models.Model):
    """
    Permission flags are predefined (in the code) flags of user rights.
    Very similar to django's permissions.

    (I decided against using django's permissions for the sake of simplicity..
    i don't like the idea of auto generating permissions which aren't used
    in the application code (but only within the django administration))
    """
    name = models.CharField( ugettext_lazy(u'Name'), max_length = 250, unique = True )


    sph_permission_flags = { 'group_administrator':
                             ugettext_lazy('Users with this permission flag have all permissions.'),

                             'community_manage_roles':
                             ugettext_lazy('User has permission to create, edit and assign roles.'),

                             'community_manage_users':
                             ugettext_lazy('User has permission to manage other users'),
                             }


    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = ugettext_lazy('Permission flag')
        verbose_name_plural = ugettext_lazy('Permission flags')


class Role(models.Model):
    """
    A role is a user defined collection of so called permission flags.
    """
    name = models.CharField(ugettext_lazy(u'Name'), max_length = 250)
    group = models.ForeignKey(Group, verbose_name=ugettext_lazy(u'Group'))

    permission_flags = models.ManyToManyField( PermissionFlag, related_name = 'roles', verbose_name=ugettext_lazy(u'Permission flags'))


    def get_permission_flag_string(self):
        return ", ".join( [flag.name for flag in self.permission_flags.all()] )

    def __unicode__(self):
        return '%s - %s' % (self.group.name, self.name)

    def get_absolute_editurl(self):
        return ('sphene.community.views.admin_permission_role_edit', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_editurl = sphpermalink(get_absolute_editurl)

    def get_absolute_memberlisturl(self):
        return ('sphene.community.views.admin_permission_role_member_list', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_memberlisturl = sphpermalink(get_absolute_memberlisturl)

    def get_absolute_memberaddurl(self):
        return ('sphene.community.views.admin_permission_role_member_add', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_memberaddurl = sphpermalink(get_absolute_memberaddurl)

    def get_absolute_groupmemberaddurl(self):
        return ('sphene.community.views.admin_permission_role_groupmember_add', (), { 'groupName': self.group.name, 'role_id': self.id, } )
    get_absolute_groupmemberaddurl = sphpermalink(get_absolute_groupmemberaddurl)

    class Meta:
        verbose_name = ugettext_lazy(u'Role')
        verbose_name_plural = ugettext_lazy(u'Roles')
        unique_together = (('name', 'group'),)


class RoleMember(models.Model):
    """
    A role member is the relation between a given role and a 
    1.) user OR 2.) rolegroup - one of those two have to be null !

    This relation can have additional limitations - e.g. for the board
    it might only be active within one given category -
    see RoleMemberLimitation.

    If there are no limitations (has_limitations = False) then the role
    is active for the user globally within the role's group.
    """
    role = models.ForeignKey(Role, verbose_name=ugettext_lazy(u'Role'))
    user = models.ForeignKey(User, null=True, verbose_name=ugettext_lazy(u'User'))
    rolegroup = models.ForeignKey('RoleGroup', null=True, verbose_name=ugettext_lazy(u'Role group'))

    has_limitations = models.BooleanField(ugettext_lazy(u'Has limitations'))


    changelog = ( ( '2008-04-15 00', 'alter', 'ALTER user_id DROP NOT NULL', ),
                  ( '2008-04-15 01', 'alter', 'ADD rolegroup_id integer REFERENCES community_rolegroup(id)', ), )

    def get_limitations_string(self):
        if not self.has_limitations:
            return "None"
        limitation = self.rolememberlimitation_set.get()
        return "%s: %s" % (limitation.object_type.model_class()._meta.object_name, unicode(limitation.content_object))

    class Meta:
        verbose_name = ugettext_lazy('Role member')
        verbose_name_plural = ugettext_lazy('Role members')


class RoleMemberLimitation(models.Model):
    """
    Limits the membership of a user to a role by only applying to a
    specific object.
    """
    role_member = models.ForeignKey(RoleMember, verbose_name=ugettext_lazy(u'Role member'))

    object_type = models.ForeignKey(ContentType, verbose_name=ugettext_lazy(u'Object type'))
    object_id = models.PositiveIntegerField(db_index = True)

    content_object = generic.GenericForeignKey(ct_field = 'object_type')

    class Meta:
        verbose_name = ugettext_lazy('Role member limitation')
        verbose_name_plural = ugettext_lazy('Role member limitations')
        unique_together = (('role_member', 'object_type', 'object_id'),)


class RoleGroup(models.Model):
    """
    a role group can be used to add common restrictions for a given group 
    of users.
    """
    group = models.ForeignKey(Group, verbose_name=ugettext_lazy(u'Group'))
    name = models.CharField(max_length = 250)

    def __unicode__(self):
        return self.name

    def get_absolute_editurl(self):
        return ('sphene.community.views.admin_permission_rolegroup_edit', (), { 'groupName': self.group.name, 'rolegroup_id': self.id, } )
    get_absolute_editurl = sphpermalink(get_absolute_editurl)

    class Meta:
        verbose_name = ugettext_lazy('Role group')
        verbose_name_plural = ugettext_lazy('Role groups')
        unique_together = ('group', 'name',)


class RoleGroupMember(models.Model):
    rolegroup = models.ForeignKey(RoleGroup, verbose_name=ugettext_lazy(u'Role group'))
    user = models.ForeignKey(User, verbose_name=ugettext_lazy(u'User'))

    class Meta:
        verbose_name = ugettext_lazy('Role group member')
        verbose_name_plural = ugettext_lazy('Role group members')
        unique_together = ('rolegroup', 'user',)



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

    returns True if anything has changed, False otherwise.
    """

    model_type = ContentType.objects.get_for_model(model_instance)

    # Check if anything has changed
    tag_labels = list(tag_labels)
    old_tag_labels = TaggedItem.objects.filter( content_type__pk = model_type.id,
                                                object_id = model_instance.id, )

    if len(tag_labels) == old_tag_labels.count():
        if len(tag_labels) == 0:
            # Nothing has changed
            return False

        for tagged_item in old_tag_labels:
            found = False
            for tag_label in tag_labels:
                if tag_label == tagged_item.tag_label:
                    found = True
                    tag_labels.remove(tag_label)
                    break

            if not found:
                break

        if len(tag_labels) == 0:
            # We started with the same amount of tags and all are
            # the same ... ie. they did not change.
            return False


    # First remove existing tag labels
    TaggedItem.objects.filter( content_type__pk = model_type.id,
                               object_id = model_instance.id, ).delete()

    

    for tag_label in tag_labels:
        t = TaggedItem( object = model_instance,
                        tag_label = tag_label )
        t.save()


    return True


def tag_get_labels(model_instance):
    """
    returns all TagLabel objects for the given model_instance.
    """
    model_type = ContentType.objects.get_for_model(model_instance)
    tagged_items = TaggedItem.objects.filter( content_type__pk = model_type.id,
                                              object_id = model_instance.id, )

    tag_labels = list()
    for tagged_item in tagged_items:
        if tagged_item.tag_label == '':
            continue
        tag_labels.append( tagged_item.tag_label )

    return tag_labels

def tag_get_or_create_label(group, tag_label_str):
    if tag_label_str == '':
        # ignore empty labels
        return None
    
    # Check if the label is already known:
    try:
        tag_label = TagLabel.objects.get( tag__group = group,
                                          label__exact = tag_label_str )
    except TagLabel.DoesNotExist:
        # TagLabel not found, search for an appropriate tag
        tag_name_str = tag_sanitize(tag_label_str)
        # Find tag
        try:
            tag = Tag.objects.get( group = group,
                                   name__exact = tag_name_str )
        except Tag.DoesNotExist:
            tag = Tag( group = group,
                       name = tag_name_str )
            tag.save()

        tag_label = TagLabel( tag = tag,
                              label = tag_label_str )
        tag_label.save()

    return tag_label


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
    group = models.ForeignKey(Group, verbose_name=ugettext_lazy(u'Group'))
    name = models.CharField( max_length = 250, )

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = ugettext_lazy('Tag')
        verbose_name_plural = ugettext_lazy('Tags')
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
        verbose_name = ugettext_lazy('Tag label')
        verbose_name_plural = ugettext_lazy('Tag labels')
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
        verbose_name = ugettext_lazy('Tagged item')
        verbose_name_plural = ugettext_lazy('Tagged items')
        unique_together = (('tag_label', 'content_type', 'object_id'))

#########################################################
###
### hooks
###

from django import forms
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display


def get_public_emailaddress_help():
    # TODO also add a notice about wether anonymous user require to enter a captcha ?
    if get_sph_setting( 'community_email_show_only_public' ):
        return _('This email address will be shown to all users. If you leave it black noone will see your email address.')
    return _('This email address will be shown to all users. If you leave it blank, your verified email address will be shown.')

def get_user_displayname_help():
    if get_sph_setting( 'community_user_displayname_fallback' ) == 'username':
        return _('This display name will be shown to all users. If you leave it blank then your username will be shown.')
    return _('This display name will be shown to all users. If you leave it blank, your first and last name will be shown. If those are blank too, then your username will be shown.')


def community_profile_edit_init_form(sender, instance, signal, request, *args, **kwargs):
    user = instance.user
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        profile = CommunityUserProfile( user = user, )
        
    instance.fields['community_settings'] = Separator(label=_(u'Community settings'))
    instance.fields['displayname'] = forms.CharField( label = _(u'Display name'),
                                                      required = False,
                                                      initial = profile.displayname,
                                                      help_text = get_user_displayname_help())
    
    instance.fields['public_emailaddress'] = forms.CharField( label = _(u'Public email address'),
                                                              required = False,
                                                              initial = profile.public_emailaddress,
                                                              help_text = get_public_emailaddress_help())




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
    profile.displayname = data['displayname']
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
    
    messages.success(request, message = _("Successfully saved community profile.") )

def community_profile_display(sender, signal, request, user, **kwargs):
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

profile_edit_init_form.connect(community_profile_edit_init_form, sender = EditProfileForm)
profile_edit_save_form.connect(community_profile_edit_save_form, sender = EditProfileForm)
profile_display.connect(community_profile_display)
post_save.connect(clear_user_displayname, sender=User)
post_save.connect(clear_user_displayname, sender=CommunityUserProfile)

# permissions cache handlers
post_save.connect(clear_permissions_cache_rgm, sender=RoleGroupMember)
post_save.connect(clear_permissions_cache_rml, sender=RoleMemberLimitation)
post_save.connect(clear_permissions_cache_rm, sender=RoleMember)

post_delete.connect(clear_permissions_cache_rgm, sender=RoleGroupMember)
post_delete.connect(clear_permissions_cache_rml, sender=RoleMemberLimitation)
post_delete.connect(clear_permissions_cache_rm, sender=RoleMember)

post_save.connect(clear_permission_flag_cache, sender=Role)
post_delete.connect(clear_permission_flag_cache, sender=Role)
