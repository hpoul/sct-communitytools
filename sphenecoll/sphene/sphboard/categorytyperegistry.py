


class CategoryType(object):
    """
    Base class for all category types.
    """

    # The name uniqueley identifies this category type.
    name = None

    # The label which will be displayed to the user.
    label = None


category_type_registry = { }


def register_category_type(category_type):
    """
    Call this method with an instance of a CategoryType
    subclass to add a custom category type.
    """
    category_type_registry[category_type.name] = category_type

def get_category_type(category_type_name):
    """
    Returns the CategoryType instance for the given type name,
    or None if it is not known.
    """
    return category_type_registry.get(category_type_name, None)

def get_category_type_list():
    """
    Returns a list of all known category types.
    """
    return category_type_registry.values()
