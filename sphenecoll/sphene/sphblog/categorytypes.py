from django import newforms as forms
from django.utils.safestring import mark_safe

from sphene.community.fields import TagField
from sphene.community.widgets import TagWidget

from sphene.sphboard.views import PostForm
from sphene.sphboard.categorytyperegistry import CategoryType, register_category_type
from sphene.sphblog.models import BlogPostExtension, BLOG_POST_STATUS_CHOICES
from sphene.sphblog.utils import slugify

class BlogPostForm(PostForm):
    slug = forms.CharField(required = False,
                           help_text = "Optionally define a slug for this blog post. Otherwise it will be filled automatically.")
    status = forms.ChoiceField(choices = BLOG_POST_STATUS_CHOICES,
                               initial = 2)
    tags = TagField(required = False)

    def clean_slug(self):
        if not 'subject' in self.cleaned_data:
            raise forms.ValidationError( 'No subject to generate slug.' )
        slug = self.cleaned_data['slug']
        if slug == '':
            slug = slugify(self.cleaned_data['subject'])
        else:
            try:
                BlogPostExtension.objects.get( slug__exact = slug )
                raise forms.ValidationError( 'Slug is already in use.' )
            except BlogPostExtension.DoesNotExist:
                # Everything all-right
                pass
        return slug


class BlogCategoryType(CategoryType):
    name = "sphblog"

    label = "Blog Category"

    def get_post_form_class(self, replypost, editpost):
        if replypost is not None and \
                (editpost is None or editpost.thread is not None):
            # If we are posting a reply, use the default PostForm
            return PostForm
        return BlogPostForm

    def save_post(self, newpost, data):
        super(BlogCategoryType, self).save_post(newpost, data)
        if newpost.thread is not None:
            return
        try:
            ext = newpost.blogpostextension_set.get()
        except BlogPostExtension.DoesNotExist:
            ext = BlogPostExtension( post = newpost, )

        ext.slug = data['slug']
        ext.status = data['status']
        ext.save()

    def get_absolute_url_for_post(self, post):
        return post.blogpostextension_set.get().get_absolute_url()


def doinit():
    """ This method is called from __init__.py """
    print "initializing linklist category type ..."
    register_category_type(BlogCategoryType)

