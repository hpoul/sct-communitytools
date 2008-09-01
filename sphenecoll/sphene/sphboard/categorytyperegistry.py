from django.db.models import signals, get_apps, get_models
from django.conf import settings


class CategoryTypeBase(type):
    "Metaclass for all category types"
    def __new__(cls, name, bases, attrs):
        # If this isn't a subclass of Model, don't do anything special.
        new_class = super(CategoryTypeBase, cls).__new__(cls, name, bases, attrs)
        try:
            parents = [b for b in bases if issubclass(b, CategoryType)]
            if not parents:
                return new_class
        except NameError:
            # 'Model' isn't defined yet, meaning we're looking at Django's own
            # Model class, defined below.
            return new_class

        register_category_type(new_class)
        return new_class


class CategoryType(object):
    """
    Base class for all category types.
    """

    __metaclass__ = CategoryTypeBase

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
        Should return a 'forms' form instance - a subclass of 
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

    def get_absolute_url_for_post(self, post):
        """
        Allows implementors to hook into the get_absolute_url() method of a Post
        """
        return None

    def get_absolute_url_for_category(self):
        """
        should return the absolute url for self.category
        """
        return None


    def append_edit_message_to_post(self, post):
        """
        Determines if an 'edit message' should be appended to a post the user has just 
        modified.
        """
        return True

    def is_displayed(self):
        """
        Return True if it should be displayed in overviews,
        False otherwise.
        """
        return True


category_type_registry = { }
initialized = False


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
    __assure_initialized();
    return category_type_registry.get(category_type_name, None)

def get_category_type_list():
    """
    Returns a list of all known category types.
    """
    __assure_initialized();
    return category_type_registry.values()

def __assure_initialized():
    if not initialized: #category_type_registry:
        __init_category_types()

def __init_category_types():
    # for now use settings.INSTALLED_APPS
    # but in the end we should better use get_apps() ?

    for app_name in settings.INSTALLED_APPS:
        mod = __import__(app_name, {}, {}, ['categorytypes'])
        if hasattr(mod, 'categorytypes'):
            initialized = True
            #print "We found categorytypes in %s" % app_name


#    apps = get_apps()
#    for app in apps:
#        try:
#            app.categorytypes
#            print "Wanting to search in %s - %s" % (type(app),str(app))
#        except AttributeError:
#            pass

#        mod = __import__(app
