from django import template
from django.utils.translation import ugettext_lazy

from sphene.community.templatetagutils import SimpleRetrieverNode, simple_retriever_tag
from sphene.community.middleware import get_current_user, get_current_group

from sphene.generic import advanced_object_list as objlist

from sphene.sphboard.models import ThreadInformation
from sphene.sphboard.lists import ThreadList

from sphene.sphcomments.models import CommentsCategoryConfig

register = template.Library()


def get_commentinfos(obj, context):
    # find the right category
    categoryconfig = CommentsCategoryConfig.objects.get_or_create_for_object(
        obj)
    threads = ThreadInformation.objects.filter(
        category = categoryconfig.category,
        root_post__is_hidden=0) \
        .select_related('root_post', 'latest_post')
    request = context['request']
    threadlist = ThreadList(objlist.QuerySetProvider(threads),
                            object_name = ugettext_lazy( 'Threads' ),
                            prefix = 'threadlist_comments',
                            cssclass = 'threadlist',
                            session = request.session,
                            requestvars = request.GET,
                            defaultsortby = 'latestpostdate',
                            defaultsortorder = 'desc',
                            defaultcolconfig = ( 'newpost',
                                                 ( 'subject',
                                                   'author', ),
                                                 'views',
                                                 'posts', 
                                                 ( 'latestpostdate',
                                                   'latestpostauthor', ), ), )
    
    context['threadlist'] = threadlist
    context['category'] = categoryconfig.category
    context['allowPostThread'] = categoryconfig.category.has_post_thread_permission()


@register.tag(name="sphcomments_load_infos")
def sphcomments_load_infos(parser, token):
    return simple_retriever_tag(parser, token, 'sphcomments_load_infos', get_commentinfos)


