from django.db.models import get_app, get_models
from sphene.sphboard import models
from django.conf import settings
import os

def init_data(app, created_models, verbosity, **kwargs):
    from sphene.community.models import Group
    from sphene.sphboard.models import Category, ThreadInformation
    os.environ['sph_init_data'] = 'true'
    if Category in created_models:
        group, created = Group.objects.get_or_create( name = 'example',
                                                      longname = 'Example Group',
                                                      baseurl = 'www.example.com', )

        category, created = Category.objects.get_or_create( name = 'Example Category',
                                                   group = group,
                                                   description = 'This is just an example Category. You can modify categories in the django admin interface.',
                             )

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

# handle both post_syncdb and post_migrate (if south is used)
def syncdb_compat(app_label, handler=None, *args, **kwargs):
    if app_label=='sphboard':
        app = get_app(app_label)
        models = get_models(app)
        handler(app=app, created_models=models, verbosity=1, **kwargs)

def syncdb_compat_init_data(app, *args, **kwargs):
    syncdb_compat(app, handler=init_data, *args, **kwargs)

def syncdb_compat_do_changelog(app, *args, **kwargs):
    syncdb_compat(app, handler=do_changelog, *args, **kwargs)

if 'south' in settings.INSTALLED_APPS:
    from south.signals import post_migrate
    post_migrate.connect(syncdb_compat_init_data)
    post_migrate.connect(syncdb_compat_do_changelog)
else:
    from django.db.models.signals import post_syncdb
    post_syncdb.connect(do_changelog, sender=models)
    post_syncdb.connect(init_data, sender=models)
