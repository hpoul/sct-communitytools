from django import newforms as forms
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from sphene.community.widgets import TagWidget
from sphene.community.models import Tag, TagLabel, tag_sanitize
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

            # Check if the label is already known:
            try:
                tag_label = TagLabel.objects.get( tag__group = get_current_group(),
                                                  label__exact = tag_label_str )
            except TagLabel.DoesNotExist:
                # TagLabel not found, search for an appropriate tag
                tag_name_str = tag_sanitize(tag_label_str)
                # Find tag
                try:
                    tag = Tag.objects.get( group = get_current_group(),
                                           name__exact = tag_name_str )
                except Tag.DoesNotExist:
                    tag = Tag( group = get_current_group(),
                               name = tag_name_str )
                    tag.save()

                tag_label = TagLabel( tag = tag,
                                      label = tag_label_str )
                tag_label.save()

            
            tag_labels.append(tag_label)

        return tag_labels

