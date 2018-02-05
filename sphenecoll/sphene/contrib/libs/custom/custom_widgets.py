import json

from django.forms import *


class TinyMCE(Textarea):
    """
    TinyMCE widget. requires you include tiny_mce_src.js in your template
    you can customize the mce_settings by overwriting instance mce_settings,
    or add extra options using update_settings
    """
    mce_settings = dict(
        mode="exact",
        theme="simple",
        theme_advanced_toolbar_location="top",
        theme_advanced_toolbar_align="center",
    )

    # def update_settings(self, custom):
    #     return_dict = self.mce_settings.copy()
    #     return_dict.update(custom)
    #     return return_dict

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget as an HTML string."""
        context = self.get_context(name, value, attrs)
        res = self._render(self.template_name, context, renderer)
        self.mce_settings['elements'] = "id_%s" % name
        mce_json = json.dumps(self.mce_settings)
        res = '{} <script type="text/javascript">tinyMCE.init({})</script>'.format(res, mce_json)
        return res
