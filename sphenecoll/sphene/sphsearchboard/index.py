try:
    from djapian import space
    from djapian.indexer import Indexer
    from sphene.sphboard.models import Post

    class PostIndexer(Indexer):
        fields = [('subject', 20), 'body']
        tags = [
            ('subject', 'subject', 20),
            ('date', 'postdate'),
            ('category', 'category.name'),
            ('post_id', 'id'),
            ('category_id', 'category.id'),
            ('group_id', 'category.group.id'),
          ]

    space.add_index(Post, PostIndexer, attach_as='indexer')
except Exception as e:
    print('Exception in sphsearchboard/index.py', e)
    pass
