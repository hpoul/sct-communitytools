from django import forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _

from sphene.community.widgets import TagWidget
from sphene.community.models import Tag, TagLabel, tag_sanitize, tag_get_or_create_label
from sphene.community.middleware import get_current_group

class TagField(forms.CharField):
    widget = TagWidget

    def __init__(self, model = None, *args, **kwargs):
        if not 'help_text' in kwargs:
            kwargs['help_text'] = _(u'Comma separated list of tags.')

        widget = TagWidget
        if model is not None:
            content_type_id = ContentType.objects.get_for_model(model).id
            widget = TagWidget(content_type_id)

        super(TagField, self).__init__(widget = widget, *args, **kwargs)

    def clean(self, value):
        value = super(TagField, self).clean(value)

        if value is None:
            return value

        tag_label_strs = value.split(',')
        tag_labels = list()
        for tag_label in tag_label_strs:
            tag_label_str = tag_label.strip()

            if tag_label_str == '':
                # Ignore empty labels
                continue

            tag_label = tag_get_or_create_label(get_current_group(), tag_label_str)
            
            tag_labels.append(tag_label)

        return tag_labels

