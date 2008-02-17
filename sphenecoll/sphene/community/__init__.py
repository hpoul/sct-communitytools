
class PermissionDenied(Exception):
    pass




from django.dispatch import dispatcher
# We can't import it as 'forms' because we've got a package called 'forms' .. how smart.
from django import newforms as djangoforms
from django.conf import settings
from sphene.community.forms import EditProfileForm, Separator
from sphene.community.signals import profile_edit_init_form, profile_edit_save_form, profile_display
from sphene.community.sphutils import get_sph_setting
from sphene.community.models import CommunityUserProfile
from sphene.community import sphsettings


jsincludes = get_sph_setting( 'community_jsincludes', [])
jsincludes.append(settings.MEDIA_URL + 'sphene/community/jquery.pack.js')
jsincludes.append(settings.MEDIA_URL + 'sphene/community/jquery.autocomplete.js')
sphsettings.set_sph_setting( 'community_jsincludes', jsincludes )


####
#
# Source code for adding an avatar .. (advanced community profile)
#

def clean_community_advprofile_avatar(self):
    f = self.cleaned_data['community_advprofile_avatar']
    if f is None:
        return f

    # Verify file size ..
    size = len(self.cleaned_data['community_advprofile_avatar'].content)
    max_size = get_sph_setting( 'community_avatar_max_size' )
    if size > max_size:
        raise djangoforms.ValidationError( "Max upload filesize of %d bytes exceeded. (Your file had %d bytes)" % (max_size, size) )

    from PIL import Image
    from cStringIO import StringIO

    try:
        # Verify image dimensions ..
        image = Image.open(StringIO(f.content))
        width = image.size[0]
        height = image.size[1]

        max_width = get_sph_setting( 'community_avatar_max_width' )
        max_height = get_sph_setting( 'community_avatar_max_height' )

        if width > max_width or height > max_height:
            raise djangoforms.ValidationError( "Max size of %dx%d exceeded (Your upload was %dx%d)" % (max_width, max_height, width, height) )
        
    except IOError:
        raise ValidationError( "Uploaded an invalid image." )
    
    return f

def community_advprofile_edit_init_form(sender, instance, signal, *args, **kwargs):
    user = instance.user
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        profile = CommunityUserProfile( user = user, )

    if profile.avatar:
        instance.fields['community_advprofile_avatar_remove'] = djangoforms.BooleanField( label = 'Delete avatar', required = False )

    instance.fields['community_advprofile_avatar'] = djangoforms.ImageField( label = 'Avatar', required = False, )
    instance.clean_community_advprofile_avatar = lambda : clean_community_advprofile_avatar(instance)

def community_advprofile_edit_save_form(sender, instance, signal, request):
    data = instance.cleaned_data
    user = instance.user
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        profile = CommunityUserProfile( user = user, )

    if profile.avatar and data['community_advprofile_avatar_remove']:
        # TODO: delete avatar file from disk.
        profile.avatar = None

    if data['community_advprofile_avatar']:
        profile.save_avatar_file( data['community_advprofile_avatar'].filename, data['community_advprofile_avatar'].content )
    #profile.avat = data['public_emailaddress']
    profile.save()


from sphene.community.templatetags import sph_extras

def community_advprofile_display(sender, signal, request, user):
    try:
        profile = CommunityUserProfile.objects.get( user = user, )
    except CommunityUserProfile.DoesNotExist:
        return None

    avatar = None
    avatar_width = None
    avatar_height = None
    if not profile.avatar:
        default_avatar = get_sph_setting( 'community_avatar_default' )
        if not default_avatar:
            return None
        avatar = default_avatar
        avatar_width = get_sph_setting( 'community_avatar_default_width' )
        avatar_height = get_sph_setting( 'community_avatar_default_height' )
    else:
        avatar = profile.get_avatar_url()
        avatar_width = profile.avatar_width
        avatar_height = profile.avatar_height
        
    
    ret = ''

    ret = '<tr><th>Avatar</th><td><img src="%s" width="%dpx" height="%dpx" alt="Users avatar"></img></td></tr>' % (avatar, avatar_width, avatar_height)
    
    return ret

dispatcher.connect(community_advprofile_edit_init_form, signal = profile_edit_init_form, sender = EditProfileForm)
dispatcher.connect(community_advprofile_edit_save_form, signal = profile_edit_save_form, sender = EditProfileForm)
dispatcher.connect(community_advprofile_display, signal = profile_display)


