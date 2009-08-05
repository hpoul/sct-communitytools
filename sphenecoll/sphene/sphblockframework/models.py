
# Models used by the block framework

from django.db import models
from django.contrib.auth.models import User

from sphene.community.middleware import get_current_group, get_current_request
from sphene.community.sphutils import sphpermalink
from sphene.community.models import Group

from sphene.sphblockframework import blockregistry



def get_or_create_page_configuration(group):
    try:
        return PageConfiguration.objects.get(group = group)
    except PageConfiguration.DoesNotExist:
        pc = PageConfiguration(group = group, user_configurable = 1)
        pc.save()
        return pc

def get_region(group, user, name):
    pc = get_or_create_page_configuration(group)

    pci = None
    try:
        if user.is_authenticated():
            pci = PageConfigurationInstance.objects.get(
                page_configuration = pc,
                user = user)
    except PageConfigurationInstance.DoesNotExist:
        pass

    if pci is None:
        try:
            pci = PageConfigurationInstance.objects.get(
                page_configuration = pc,
                user__isnull = True )
        except PageConfigurationInstance.DoesNotExist:
            pci = PageConfigurationInstance(
                page_configuration = pc)
            pci.save()

    try:
        return BlockRegion.objects.get(config_instance = pci,
                                       name = name)
    except BlockRegion.DoesNotExist:
        return None


def get_or_create_region(group, user, name):
    if not user.is_authenticated:
        return None
    page_config = get_or_create_page_configuration(group)
    if not page_config.user_configurable:
        return None

    # Create configuration instance ..
    try:
        ci = PageConfigurationInstance.objects.get(
            page_configuration = page_config,
            user = user)
    except PageConfigurationInstance.DoesNotExist:
        ci = PageConfigurationInstance(page_configuration = page_config,
                                       user = user)
        ci.save()

    try:
        return BlockRegion.objects.get(config_instance = ci,
                                       name = name)
    except BlockRegion.DoesNotExist:
        region = BlockRegion(config_instance = ci,
                             name = name)
        region.save()
        return region

class PageConfiguration(models.Model):
    group = models.ForeignKey(Group)
    user_configurable = models.IntegerField()


class PageConfigurationInstance(models.Model):
    page_configuration = models.ForeignKey(PageConfiguration)
    user = models.ForeignKey(User, null = True)

    class Meta:
        unique_together = (('page_configuration', 'user'))


class BlockRegion(models.Model):
    name = models.CharField(max_length = 250)
    config_instance = models.ForeignKey(PageConfigurationInstance)


class BlockChoices(object):
    def __iter__(self):
        choices = ()

        for block in blockregistry.get_block_list():
            choices += ((block.name, block.label),)

        return choices.__iter__()


class BlockConfigurationManager(models.Manager):

    def all_available(self):
        return self.filter(page_configuration__group = get_current_group)


class BlockConfiguration(models.Model):
    page_configuration = models.ForeignKey(PageConfiguration)
    label = models.CharField(max_length = 250, blank = True, help_text = 'Leave blank to use default label.')
    block_name = models.CharField(max_length = 250, db_index = True, choices = BlockChoices() )
    config_value = models.CharField(max_length = 250, help_text = "Used for configuration for very simple blocks.", blank = True)

    objects = BlockConfigurationManager()

    def get_label(self):
        if not self.label:
            return self.get_block().label
        return self.label

    def get_block(self):
        return blockregistry.get_block(self.block_name)

    def get_absolute_edit_url(self):
        return ('sphene.sphblockframework.views.edit_block_config', (), { 'block_config_id': self.id })
    get_absolute_edit_url = sphpermalink(get_absolute_edit_url)


class BlockInstancePosition(models.Model):
    region = models.ForeignKey(BlockRegion)
    block_configuration = models.ForeignKey(BlockConfiguration)
    sortorder = models.IntegerField()

    def get_label(self):
        return self.block_configuration.get_label()

    def get_block_instance(self):
        return self.block_configuration.get_block()(self)

    def render(self):
        return self.get_block_instance().render()

    class Meta:
        ordering = ['sortorder']


