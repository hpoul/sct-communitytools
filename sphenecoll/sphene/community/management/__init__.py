from django.apps import apps
from sphene.community import models
from django.db.models.signals import post_migrate
from sphene.community.models import PermissionFlag, Role, Group


