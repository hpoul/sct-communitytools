
import logging
import os


from django.conf import settings

from sphene.community import sphsettings
from sphene.community.middleware import get_current_group, get_current_user
from sphene.sphboard.models import Post, get_all_viewable_categories


logger = logging.getLogger('sphene.sphsearchboard.models')

post_index = None
try:
    import urls  #ensure that load_indexes is called
    post_index= Post.indexer
except:
    from djapian import Indexer
    searchboard_post_index = sphsettings.get_sph_setting('sphsearchboard_post_index', '/var/cache/sct/postindex/')

    if not os.path.isdir(searchboard_post_index):
        os.makedirs(searchboard_post_index)

    Post.index_model = 'sphene.sphsearchboard.models.post_index'
    post_index = Indexer(
        path = searchboard_post_index,

        model = Post,

        fields = [('subject', 20), 'body'],

        tags = [
            ('subject', 'subject', 20),
            ('date', 'postdate'),
            ('category', 'category.name'),
            ('post_id', 'id'),
            ('category_id', 'category.id'),
            ('group_id', 'category.group.id'),
          ])


    post_index.boolean_fields = ('category_id', 'group_id',)

class PostFilter(object):
    """
    Very simplistic "filter" for the search resultset
    - since this is only a security measure to ensure the
    search string got recognized we simply filter out 
    everything that is not in the viewable categries.

    this could lead to weird display behaviors.. but
    only if the search query didn't match es expected.
    """

    def __init__(self, resultset, viewable_category_ids):
        self.resultset = resultset
        self.viewable_category_ids = viewable_category_ids

    def __len__(self):
        return self.resultset.count()
    count = __len__


    def __iter__(self):
        for hit in self.resultset:
            if self.verify_hit(hit):
                yield hit

    def verify_hit(self, hit):
        return hit.instance.category_id in self.viewable_category_ids

    def __getslice__(self, start, end):
        for hit in self.resultset[start:end]:
            if self.verify_hit(hit):
                yield hit


def search_posts(query, category = None):
    group = get_current_group()
    user = get_current_user()
    #if group:
    #    query = u''.join((u'+', u'group_id:', unicode(group.id), ' ', query))
    categories = get_all_viewable_categories(group, user)
    if category is not None:
        prefix = u'category_id:%d' % category.id
    else:
        prefix = u' OR '.join([u'category_id:%d' % category for category in categories])
    query = u'(%s) AND (%s)' % (prefix, query)
    logger.debug('Searching for: %s' % query)
    ret = PostFilter(post_index.search(query=query), categories)
    logger.debug('Searching done.')
    return ret


def get_category_name(post):
    return post.category.name
get_category_name.name = 'category'

def get_category_id(post):
    return post.category.id
get_category_id.name = 'category_id'

def get_group_id(post):
    return post.category.group.id
get_group_id.name = 'group_id'
