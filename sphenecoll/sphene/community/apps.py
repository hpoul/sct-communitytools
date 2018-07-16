import logging

from django.apps import AppConfig, apps as apps_root
from django.db.models.signals import post_migrate
from django.db import router

logger = logging.getLogger('sphene.community.apps')

class CommunityConfig(AppConfig):
    name = u'sphene.community'
    verbose_name = u"Community"

    def ready(self):
        import sphene.community.signals.handlers

        post_migrate.connect(init_data, sender=self, dispatch_uid="communitytools.sphenecoll.sphene.community.management")
        post_migrate.connect(create_permission_flags, sender=self)


# noinspection PyPep8Naming
def init_data(apps, verbosity, using, **kwargs):
    Group = apps.get_model('community', 'Group')
    Navigation = apps.get_model('community', 'Navigation')
    CommunityUserProfileField = apps.get_model('community', 'CommunityUserProfileField')

    if not router.allow_migrate(using, Group):
        logger.info('Not allowed migration for Group.')
        return

    logger.info('allowing %s migrate? %s', using, repr(router.allow_migrate(using, Group)))

    if Group.objects.count() > 0:
        return

    group, created = Group.objects.get_or_create(name='example',
                                                 longname='Example Group',
                                                 baseurl='www.example.com', )
    group.save()

    nav = Navigation(group=group,
                     label='Home',
                     href='/wiki/show/Start/',
                     urltype=0,
                     sortorder=10,
                     navigationType=0,
                     )
    nav.save()

    nav = Navigation(group=group,
                     label='Board',
                     href='/board/show/0/',
                     urltype=0,
                     sortorder=20,
                     navigationType=0,
                     )
    nav.save()

    CommunityUserProfileField(name='ICQ UIN',
                              regex='\d+',
                              sortorder=100, ).save()
    CommunityUserProfileField(name='Jabber Id',
                              regex='.+@.+',
                              sortorder=200, ).save()
    CommunityUserProfileField(name='Website URL',
                              regex='http://.*',
                              sortorder=300,
                              renderstring='<a href="%(value)s">%(value)s</a>', ).save()


def create_permission_flags(apps, verbosity, **kwargs):
    """
    Creates permission flags by looking at the Meta class of all models.

    These Meta classes can have a 'sph_permission_flags' attribute containing
    a dictionary with 'flagname': 'some verbose userfriendly description.'

    Permission flags are not necessarily bound to a given model. It just needs
    to be assigned to one so it can be found, but it can be used in any
    context.
    """
    from sphene.community.models import PermissionFlag, Group, Role
    for myapp in apps.get_app_configs():
        app_models = myapp.get_models()
        if not app_models:
            continue

        for klass in app_models:
            logger.debug('Checking %s for sph_permission_flags', repr(klass))
            concrete_class = apps_root.get_model(klass._meta.app_label, klass._meta.model_name)
            if hasattr(concrete_class, 'sph_permission_flags'):
                sph_permission_flags = concrete_class.sph_permission_flags

                # permission flags can either be a dictionary with keys beeing
                # flag names, values beeing the description
                # or lists in the form: ( ( 'flagname', 'description' ), ... )
                if isinstance(sph_permission_flags, dict):
                    sph_permission_flags = sph_permission_flags.items()

                for (flag, description) in sph_permission_flags:
                    flag, created = PermissionFlag.objects.get_or_create(name = flag)
                    if created and verbosity >= 2:
                        print("Added sph permission flag '%s'" % flag.name)

    if True: #Role in created_models:
        # Create a 'Group Admin' role for all groups.
        rolename = 'Group Admin'
        permissionflag = PermissionFlag.objects.get(name = 'group_administrator')
        groups = Group.objects.all()
        for group in groups:
            role, created = Role.objects.get_or_create( name = rolename, group = group )
            if not created:
                continue

            role.save()
            role.permission_flags.add(permissionflag)
            role.save()

            if verbosity >= 2:
                print("Created new role '%s' for group '%s' and assigned permission '%s'" % (rolename, group.name, permissionflag.name))
