
class CategoryType(object):
    """
    Base class for all category types.
    """

    # The name uniqueley identifies this category type.
    name = None

    # The label which will be displayed to the user.
    label = None


    def __init__(self, category):
        self.category = category


    def get_threadlist_template(self):
        """
        Allows subclasses to use a completely different template.

        The suggsted approach is to use a custom template which extends
        sphene/sphboard/listCategories.html and simply overwrite the
        required blocks.
        """
        return 'sphene/sphboard/listCategories.html'

    def get_new_thread_link_template(self):
        return 'sphene/sphboard/_new_thread_link.html'

    def get_show_thread_template(self):
        """
        The suggestd approach is to use a custom template which extends
        sphene/sphboard/showThread.html and only overwrite required blocks.
        """
        return 'sphene/sphboard/showThread.html'

    def get_post_form_class(self, replypost, editpost):
        """
        Should return a 'newforms' form instance - a subclass of 
        sphene.sphboard.views.PostForm

        Arguments:
        replypost: The post to which this form should reply to.
        editpost: The post which is edited (or None)

        To test if the user edits/creates a new reply to a thread 
        (instead of creating a new thread) you can use the following code:
        if replypost is not None and \
                (editpost is None or editpost.thread is not None):
        """
        return None

    def save_post(self, newpost, data):
        """
        This is called right after a 'Post' was saved, and so allows
        this category type to store additional data in it's own entity.

        Arguments:
        post: The post to which the user replies to.
        newpost: the new Post object which was just saved/created.
        data: the cleaned_data of the form.
        """
        pass



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
