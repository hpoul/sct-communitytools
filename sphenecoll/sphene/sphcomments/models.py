

from django.db import models
from django.db.models import signals
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


from sphene.community.middleware import get_current_group

from sphene.sphboard.models import Post, Category

# "cache" for the root category ids
# a dictionary with the group id as key.
root_category_id = {}

class CommentsCategoryConfigManager(models.Manager):
    
    def get_or_create_for_object(self, model_instance):
        # Find a category associated with the given object
        model_type = ContentType.objects.get_for_model(model_instance)
        try:
            return self.filter(object_type__pk = model_type.id,
                               object_id = model_instance.pk).get()
        except CommentsCategoryConfig.DoesNotExist:
            # Find root category
            group = get_current_group()
            from sphene.sphcomments.categorytypes import CommentsCategoryType, CommentsOnObjectCategoryType
            if not group.id in root_category_id:
                try:
                    root_category_id[group.id] = Category.objects.get(
                        group = group,
                        category_type = CommentsCategoryType.name, ).id
                except Category.DoesNotExist:
                    raise Exception('Please create a category of type "%s" (%s).' % (CommentsCategoryType.label, CommentsCategoryType.name))

            # create a new category ...
            # to copy preferences we need the root category ..
            root_category = Category.objects.get(pk = root_category_id[group.id])
            # TODO role permissions are currently not copied ..
            category = Category(
                name = 'comment category for "%s"' % unicode(model_instance),
                parent = root_category,
                group = group,
                category_type = CommentsOnObjectCategoryType.name,
                allowview = root_category.allowview,
                allowthreads = root_category.allowthreads,
                allowreplies = root_category.allowreplies, )
            category.save()
            config = CommentsCategoryConfig(category = category,
                                            content_object = model_instance)
            config.save()
            return config


class CommentsCategoryConfig(models.Model):
    category = models.ForeignKey(Category, unique = True, related_name = 'sphcomments_config')

    object_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index = True)

    content_object = generic.GenericForeignKey(ct_field = 'object_type')


    objects = CommentsCategoryConfigManager()

    class Meta:
        unique_together = (('category', 'object_type', 'object_id'),)



def clear_root_category_cache(instance, **kwargs):
    # TODO - This is a 'bit' flawed because it only works on single-process
    # installations.. which is pretty unrealistic
    # We should probably use django caching for this !
    root_category_id = {}

signals.post_save.connect(clear_root_category_cache,
                   sender = Category)
                   
signals.post_delete.connect(clear_root_category_cache,
                   sender = Category)
