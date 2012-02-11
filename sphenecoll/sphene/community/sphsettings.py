
from django.conf import settings

sph_settings_defaults = {
    # Only settings for the 'community' applications are defined here,
    # (or global settings) -- all other defaults should be added using
    # the add_setting_defaults method !

    
    'django096compatibility': False,
    
    
    'community_avatar_default': settings.STATIC_URL + 'sphene/community/default_avatar.png',
    'community_avatar_default_width': 48,
    'community_avatar_default_height': 48,
    'community_avatar_max_width': 150,
    'community_avatar_max_height': 150,
    'community_avatar_max_size': 150*1024,
    'community_avatar_upload_to': 'var/sphene/sphwiki/attachment/%Y/%m/%d',

    # Can either be 'None' so we only look into the database,
    # or can point to a directory.. if it points to a directory it tries to load
    # $(dir)/$(groupName)/$(templateName)
    'community_groupaware_template_dir': None,

    # If True, the group name is set in the URL
    'community_groups_in_url': False,

    # used by sphene.community.views.groupaware_redirect_to which looks up this variable
    # expecting a dictionary containing { 'groupname': '/redirect/url/' }
    'community_groupaware_startpage': None,

    # set this option to True if you want to only show a users email address if he
    # as entered it into the 'public email address' field - never show the
    # validated email address.
    'community_email_show_only_public': False,

    # If this option is set to true anonymous users will have to enter
    # a captcha before they are displayed the email address of a user.
    # This makes only sense if captcha support is enabled !
    'community_email_anonymous_require_captcha': False,

    # If this option is set to true and captcha support is enabled new users
    # will be asked for a captcha before a new registration email will be accepted.
    'community_register_require_captcha': False,
    
    # The time in seconds an anonymous user is allowed to see email addresses
    # before revalidating a captcha again.
    'community_email_anonymous_require_captcha_timeout': 10 * 60,
    
    # Valid options for this parameter are 'username' and 'fullname'. Any other
    # option won't cause any effect. Default value is 'fullname'.
    # This option determines the fallback sequence for displaing the name of a user:
    # let's you overwrite the displayname - has to be a reference to a function which will receive the django user object as first (and only argument)
    'community_user_get_displayname': None,

    # let's you overwrite the avatar - has to be a reference to a function - it will receive the django user object and has to return a dictionary with { 'url': '...', 'width': 123, 'height': 123 }
    'community_user_get_avatar': None,

    # 1. sequence for 'username': displayfield (if set) - username
    # 2. sequence for 'fullname': displayfield (if set) - fullname (if first or last name are set) - username
    'community_user_displayname_fallback': 'fullname',
    # name of default group created by sphene
    'default_group_name':'example',

    }


def add_setting_defaults(newdefaults):
    """
    This method can be used by other applications to define their
    default values.
    
    newdefaults has to be a dictionary containing name -> value of
    the settings.
    """
    sph_settings_defaults.update(newdefaults)


def set_sph_setting(name, value):
    if not hasattr(settings, 'SPH_SETTINGS'):
        settings.SPH_SETTINGS = {}
    settings.SPH_SETTINGS[name] = value
    

def get_sph_setting(name, default_value = None):
    if not hasattr(settings, 'SPH_SETTINGS'):
        return sph_settings_defaults.get(name, default_value)

    # TODO this needs to be done more efficient !
    return settings.SPH_SETTINGS.get(name, sph_settings_defaults.get(name, default_value))

