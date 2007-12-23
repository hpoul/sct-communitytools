# The categorytype which represents this linklist.

from django import newforms as forms
from django.utils.safestring import mark_safe

from sphene.community.templatetags.sph_extras import sph_truncate
from sphene.sphboard.categorytyperegistry import CategoryType, register_category_type
from sphene.sphboard.views import PostForm
from sphene.sphboard.categorytypes import ExtendedCategoryType, ExtendedPostForm
#from sphene.sphlinklist.models import LinkListCategoryConfig
from sphene.sphlinklist.models import LinkListPostExtension

class LinkListPostForm(ExtendedPostForm):
    link = forms.URLField(initial = 'http://', 
                          help_text = 'Enter your link here')

    def __init__(self, *args, **kwargs):
        super(LinkListPostForm, self).__init__(*args, **kwargs)
        # Is it really a good idea to do this each time ?
        self.fields.insert(1, 'link', self.fields['link'])

    def init_for_category_type(self, category_type, post):
        super(LinkListPostForm, self).init_for_category_type(category_type, post)
        if post:
            ext = post.linklistpostextension_set.get()
            self.fields['link'].initial = ext.link


class LinkListCategoryType(ExtendedCategoryType):
    name = "sphlinklist"

    label = "Link List"


    def get_post_form_class(self, replypost, editpost):
        if replypost is not None and \
                (editpost is None or editpost.thread is not None):
            # If we are posting a reply, use the default PostForm
            return PostForm
        return LinkListPostForm

    '''
    def get_linklist_config(self):
        """
        Returns a LinkListCategoryConfig object.
        If none exists yet, creates one.
        """
        try:
            config = LinkListCategoryConfig.objects.get( category = self.category )
        except LinkListCategoryConfig.DoesNotExist:
            config = LinkListCategoryConfig(category = self.category)
            config.save()
        return config
    '''

    def save_post(self, newpost, data):
        super(LinkListCategoryType, self).save_post(newpost, data)
        if newpost.thread is not None:
            return
        try:
            ext = newpost.linklistpostextension_set.get()
        except LinkListPostExtension.DoesNotExist:
            ext = LinkListPostExtension( post = newpost, )
        ext.link = data['link']
        ext.save()


    def get_threadlist_template(self):
        return 'sphene/sphlinklist/thread_list.html'

    def get_show_thread_template(self):
        return 'sphene/sphlinklist/show_thread.html'


def doinit():
    """ This method is called from __init__.py """
    print "initializing linklist category type ..."
    register_category_type(LinkListCategoryType)

