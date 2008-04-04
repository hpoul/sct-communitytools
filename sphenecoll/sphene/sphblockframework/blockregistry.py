"""
The blockregistry is responsible for finding all available blocks
in the system.
"""

from django.conf import settings
from sphene.community.middleware import get_current_request, get_current_user

class BlockBase(type):
    def __new__(cls, name, bases, attrs):
        # If this isn't a subclass of Model, don't do anything special.
        new_class = super(BlockBase, cls).__new__(cls, name, bases, attrs)
        try:
            parents = [b for b in bases if issubclass(b, Block)]
            if not parents:
                return new_class
        except NameError:
            # 'Model' isn't defined yet, meaning we're looking at Django's own
            # Model class, defined below.
            return new_class

        register_block(new_class)
        return new_class


class Block(object):
    """
    A block is a small building block within a page.
    """

    __metaclass__ = BlockBase

    #: The name which uniquely identifies this Block.
    name = None

    #: Userfriendly name for this block.
    label = None

    def __init__(self, block_position):
        self.block_position = block_position

    def render(self):
        """
        subclasses should implement this method to render
        their content. self.block_position contains the current
        position - it can also be used to access the
        BlockInstanceConfiguration model.

        (Currently) no attempt for caching is made.
        """
        pass

    def is_available(self):
        """
        should return True if this block is available for
        the current user.
        """
        return True

    def get_user(self):
        return get_current_user()

    def get_request(self):
        return get_current_request()


block_registry = {}
initialized = False

def register_block(block):
    """
    This method is called by BlockBase to register a Block.
    """
    block_registry[block.name] = block


def get_block(block_name):
    __assure_initialized()
    return block_registry[block_name]


def get_block_list():
    __assure_initialized()
    return block_registry.values()


def __assure_initialized():
    if not initialized:
        __init_blocks()


def __init_blocks():
    # for now use settings.INSTALLED_APPS
    # but in the end we should better use get_apps() ?

    for app_name in settings.INSTALLED_APPS:
        mod = __import__(app_name, {}, {}, ['blocks'])
        if hasattr(mod, 'blocks'):
            initialized = True


