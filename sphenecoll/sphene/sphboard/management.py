
from django.dispatch import dispatcher
from django.db.models import signals
from sphene.sphboard import models

def init_data(app, created_models, verbosity, **kwargs):
    from sphene.community.models import Group
    from sphene.sphboard.models import Category
    if Category in created_models:
        group = Group.objects.get( name = 'example' )
        category = Category( name = 'Example Category',
                             group = group,
                             description = 'This is just an example Category. You can modify categories in the django admin interface.',
                             )
        category.save()


dispatcher.connect(init_data, sender=models, signal=signals.post_syncdb)
