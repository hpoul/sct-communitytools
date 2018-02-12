import os

from sphene.community import sphsettings

post_index = None


def setup_indices():
    from .models import Post
    global post_index

    print('calling sphsearchboard setup_indices')

    try:
        post_index = Post.indexer
    except Exception as e:
        print(e)
        from djapian.indexer import Indexer

        searchboard_post_index = sphsettings.get_sph_setting('sphsearchboard_post_index', '/var/cache/sct/postindex/')

        if not os.path.isdir(searchboard_post_index):
            os.makedirs(searchboard_post_index)

        Post.index_model = 'sphene.sphsearchboard.models.post_index'
        post_index = Indexer(
            path=searchboard_post_index,

            model=Post,

            fields=[('subject', 20), 'body'],

            tags=[
                ('subject', 'subject', 20),
                ('date', 'postdate'),
                ('category', 'category.name'),
                ('post_id', 'id'),
                ('category_id', 'category.id'),
                ('group_id', 'category.group.id'),
            ])

        post_index.boolean_fields = ('category_id', 'group_id',)


default_app_config = 'sphene.sphsearchboard.apps.SearchBoardConfig'

