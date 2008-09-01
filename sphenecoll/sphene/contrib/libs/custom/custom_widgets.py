
from django.forms import *
from django.forms.widgets import flatatt
from django.forms.util import smart_unicode
from django.utils.html import escape
from django.utils.simplejson import *
        
class TinyMCE(Textarea):
    """
    TinyMCE widget. requires you include tiny_mce_src.js in your template
    you can customize the mce_settings by overwriting instance mce_settings,
    or add extra options using update_settings
    """ 
    
    mce_settings = dict(
        mode = "exact",
        theme = "simple",
        theme_advanced_toolbar_location = "top",
        theme_advanced_toolbar_align = "center",
    )    
             
    def update_settings(self, custom):
        return_dict = self.mce_settings.copy()
        return_dict.update(custom)
        return return_dict
    
    def render(self, name, value, attrs=None):
        if value is None: value = ''
        value = smart_unicode(value)
        final_attrs = self.build_attrs(attrs, name=name)
                   
        self.mce_settings['elements'] = "id_%s" % name
        mce_json = JSONEncoder().encode(self.mce_settings)
        
        return u'<textarea%s>%s</textarea> <script type="text/javascript">\
                tinyMCE.init(%s)</script>' % (flatatt(final_attrs), escape(value), mce_json)

