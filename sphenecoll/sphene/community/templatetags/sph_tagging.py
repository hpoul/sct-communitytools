from django import template


from sphene.community.models import tag_get_labels
from sphene.community.templatetagutils import SimpleRetrieverNode, simple_retriever_tag

register = template.Library()


@register.filter
def sph_tag_labels(value):
    return tag_get_labels(value)


def get_tag_labels(instance, context):
    return tag_get_labels(instance)


@register.tag(name="sph_tagging_get_labels")
def sphblock_get_blocks(parser, token):
    return simple_retriever_tag(parser, token, 'sph_tagging_get_labels', get_tag_labels)



