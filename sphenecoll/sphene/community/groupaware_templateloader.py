
from django.conf import settings
from django.db.models import signals
from django.dispatch import dispatcher
from django.template import TemplateDoesNotExist

from sphene.community.models import GroupTemplate, Group
from sphene.community.middleware import get_current_group

from django.core.cache import cache

def _get_cache_key(template_name, group):
    return "groupaware_templateloader_%d_%s" % (group.id, template_name)

NOT_EXIST_CACHE_VALUE = 'NOTEXIST'

# By default cache for 2 hours.
TMPL_CACHE_EXPIRE = 2 * 60 * 60

def load_template_source(template_name, template_dirs=None):
    """
    Template loader which loads templates from the database based on
    the current group.
    """
    group = get_current_group()
    if group is None:
        # If there is no current group .. we have nothing to do ..
        raise TemplateDoesNotExist(template_name)

    # Look in the cache . .so we don't have to make unnecessary database
    # queries
    cachekey = _get_cache_key(template_name, group)
    ret = cache.get( cachekey )
    if ret is not None:
        if ret == NOT_EXIST_CACHE_VALUE:
            raise TemplateDoesNotExist(template_name)
        
        return ret

    while group is not None:
        try:
            template = GroupTemplate.objects.get( template_name = template_name,
                                                  group = group, )
            ret = (template.source, "%s:%s" % (group.name, template.template_name))
            # Cache for two hours by default ..
            cache.set(cachekey, ret, TMPL_CACHE_EXPIRE)
            return ret
        except GroupTemplate.DoesNotExist:
            group = group.parent

    cache.set(cachekey, NOT_EXIST_CACHE_VALUE, TMPL_CACHE_EXPIRE)
    raise TemplateDoesNotExist(template_name)

# This loader is always usable ..
load_template_source.is_usable = True


def _recursive_clear_template_cache(template_name, group):
    cachekey = _get_cache_key( template_name, group )
    cache.delete( cachekey )
    children = Group.objects.filter( parent = group )
    for child in children:
        _recursive_clear_template_cache( template_name, child )

def clear_template_cache(instance):
    """
    Clears the template cache for the given instance, and all subgroups.
    """
    _recursive_clear_template_cache(instance.template_name, instance.group)


dispatcher.connect(clear_template_cache,
                   sender = GroupTemplate,
                   signal = signals.post_save)
