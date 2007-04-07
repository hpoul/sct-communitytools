
from django.dispatch import dispatcher
from django.db.models import signals, get_apps, get_models
from sphene.community import models

def init_data(app, created_models, verbosity, **kwargs):
    from sphene.community.models import Group
    if Group in created_models:
        group = Group( name = 'example',
                       longname = 'Example Group',
                       baseurl = 'www.example.com', )
        group.save()


def do_changelog(app, created_models, verbosity, **kwargs):
    print "TODO .. do changelog %s" % str(app)
    get_changelog = getattr(app,'get_changelog', None)
    if not get_changelog: return

    changelog = get_changelog()
    print "got changelog: %s" % str(changelog)

dispatcher.connect(init_data, sender=models, signal=signals.post_syncdb)
dispatcher.connect(do_changelog, signal=signals.post_syncdb)

