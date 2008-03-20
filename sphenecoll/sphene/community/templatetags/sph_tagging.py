from django import template


from sphene.community.models import tag_get_labels

register = template.Library()


@register.filter
def sph_tag_labels(value):
    return tag_get_labels(value)



