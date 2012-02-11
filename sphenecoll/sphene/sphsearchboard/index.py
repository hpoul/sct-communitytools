try:
    from djapian import space, Indexer
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
except:
    pass


    
