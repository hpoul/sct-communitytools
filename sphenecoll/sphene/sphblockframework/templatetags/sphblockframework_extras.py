from django import template

from sphene.community.templatetagutils import SimpleRetrieverNode, simple_retriever_tag
from sphene.community.middleware import get_current_user, get_current_group

from sphene.sphblockframework import blockregistry
from sphene.sphblockframework.models import \
    get_or_create_region, \
    get_region, \
    BlockConfiguration, \
    BlockInstancePosition

register = template.Library()



def get_blocks(blockregion, context):
    print "for region %s" % blockregion
    region = get_region(get_current_group(),
                        get_current_user(),
                        blockregion)
    block_instances = BlockInstancePosition.objects.filter(region = region,)

    context['blocks'] = block_instances

@register.tag(name="sphblock_get_blocks")
def sphblock_get_blocks(parser, token):
    return simple_retriever_tag(parser, token, 'sphblock_get_blocks', get_blocks)


def get_all_blocks(retriever, context):
    context['allblocks'] = blockregistry.get_block_list()

@register.tag(name="sphblock_get_all_blocks")
def sphblock_get_all_blocks(parser, token):
    return simple_retriever_tag(parser, token, 'sphblock_get_all_blocks', get_all_blocks)


def get_all_blockconfigs(retriever, context):
    context['allblockconfigs'] = BlockConfiguration.objects.all_available()

@register.tag(name="sphblock_get_all_blockconfigs")
def sphblock_get_all_blockconfigs(parser, token):
    return simple_retriever_tag(parser, token, 'sphblock_get_all_blockconfigs', get_all_blockconfigs)


@register.inclusion_tag('sphene/sphblockframework/_dashboard.html')
def sphblockframework_dashboard(blockregion_name):
    return { 'blockregion_name': blockregion_name,
             }
