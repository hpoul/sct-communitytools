
from django.core.management.base import NoArgsCommand

from sphene.community.signals import trigger_maintenance

class Command(NoArgsCommand):
    help = "Runs SCT maintenance tasks."

    requires_model_validation = True

    def handle_noargs(self, **options):
        trigger_maintenance()

