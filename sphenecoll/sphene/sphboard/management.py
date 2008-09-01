from django.db.models import signals

from sphene.sphboard import models

def init_data(app, created_models, verbosity, **kwargs):
    from sphene.community.models import Group
    from sphene.sphboard.models import Category, ThreadInformation, Post
    if Category in created_models:
        group = Group.objects.get( name = 'example' )
        category = Category( name = 'Example Category',
                             group = group,
                             description = 'This is just an example Category. You can modify categories in the django admin interface.',
                             )
        category.save()

    if ThreadInformation in created_models:
        # Synchronize ThreadInformation with all posts ..
        # (Required for backward compatibility)
        synchronize_threadinformation(verbosity)


def synchronize_threadinformation(verbosity = -1):
    """ Will synchronize the 'ThreadInformation' objects. """
    from sphene.sphboard.models import Category, ThreadInformation, Post, THREAD_TYPE_DEFAULT
    
    # First find all threads ...
    if verbosity >= 2:
        print "Synchronizing ThreadInformation ..."
    all_threads = Post.objects.filter( thread__isnull = True )

    for thread in all_threads:
        # Find corresponding ThreadInformation
        try:
            thread_info = ThreadInformation.objects.type_default().filter( root_post = thread ).get()
        except ThreadInformation.DoesNotExist:
            thread_info = ThreadInformation( root_post = thread,
                                             category = thread.category,
                                             thread_type = THREAD_TYPE_DEFAULT )

        thread_info.update_cache()
        thread_info.save()


from sphene.community.management import do_changelog
signals.post_syncdb.connect(do_changelog, sender=models)
signals.post_syncdb.connect(init_data, sender=models)
