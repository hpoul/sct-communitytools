
from django.dispatch import dispatcher
from django.db.models import signals
from sphene.community import models

def init_data(app, created_models, verbosity, **kwargs):
    from sphene.community.models import Group
    if Group in created_models:
        group = Group( name = 'example',
                       longname = 'Example Group',
                       baseurl = 'www.example.com', )
        group.save()


dispatcher.connect(init_data, sender=models, signal=signals.post_syncdb)
