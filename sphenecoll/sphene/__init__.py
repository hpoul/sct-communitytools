
#
# Backward compatibility to Django 0.96
# the SPH_SETTINGS['django096compatibility'] has to be set.
#
# Thanks to Dave Abrahams for this patch.

from django.conf import settings

if hasattr(settings, 'SPH_SETTINGS') and settings.SPH_SETTINGS.get('django096compatibility', False):
    from django import forms

    if not hasattr(forms.Form, 'cleaned_data'):
        def get_cleaned_data(self):
            return self.clean_data
        def set_cleaned_data(self,v):
            self.__dict__['cleaned_data'] = v
        forms.Form.cleaned_data = property(get_cleaned_data, set_cleaned_data)

