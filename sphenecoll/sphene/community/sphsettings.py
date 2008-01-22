
from django.conf import settings

sph_settings_defaults = {
    # Only settings for the 'community' applications are defined here,
    # (or global settings) -- all other defaults should be added using
    # the add_setting_defaults method !

    
    'django096compatibility': False,
    
    
    'community_avatar_default': '/static/sphene/community/default_avatar.png',
    'community_avatar_default_width': 48,
    'community_avatar_default_height': 48,
    'community_avatar_max_width': 150,
    'community_avatar_max_height': 150,
    'community_avatar_max_size': 20*1024,
    'community_avatar_upload_to': 'var/sphene/sphwiki/attachment/%Y/%m/%d',

    # Can either be 'None' so we only look into the database,
    # or can point to a directory.. if it points to a directory it tries to load
    # $(dir)/$(groupName)/$(templateName)
    'community_groupaware_template_dir': None,

    # used by sphene.community.views.groupaware_redirect_to which looks up this variable
    # expecting a dictionary containing { 'groupname': '/redirect/url/' }
    'community_groupaware_startpage': None,
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

