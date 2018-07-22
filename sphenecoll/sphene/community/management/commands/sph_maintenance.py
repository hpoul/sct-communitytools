
from django.core.management.base import BaseCommand

from sphene.community.signals import trigger_maintenance


class Command(BaseCommand):
    help = "Runs SCT maintenance tasks."

    requires_model_validation = True

    def handle(self, **options):
        trigger_maintenance()

