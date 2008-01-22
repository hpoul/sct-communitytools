from django import newforms as forms

from sphene.community.widgets import TagWidget

class TagField(forms.CharField):
    widget = TagWidget

    def __init__(self, *args, **kwargs):
        if not 'help_text' in kwargs:
            kwargs['help_text'] = 'Comma separated list of tags.'
        super(TagField, self).__init__(*args, **kwargs)
