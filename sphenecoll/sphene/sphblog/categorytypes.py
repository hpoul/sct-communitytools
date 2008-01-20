from django import newforms as forms
from django.utils.safestring import mark_safe


from sphene.sphboard.views import PostForm
from sphene.sphboard.categorytyperegistry import CategoryType, register_category_type
from sphene.sphblog.models import BlogPostExtension, BLOG_POST_STATUS_CHOICES
from sphene.sphblog.utils import slugify

class BlogPostForm(PostForm):
    slug = forms.CharField(required = False,
                           help_text = "Optionally define a slug for this blog post. Otherwise it will be filled automatically.")
    status = forms.ChoiceField(choices = BLOG_POST_STATUS_CHOICES,
                               initial = 2)

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug == '':
            print str(self.cleaned_data)
            slug = slugify(self.cleaned_data['subject'])
        else:
            try:
                BlogPostExtension.objects.get( slug__exact = slug )
                raise ValidationError( 'Slug is already in use.' )
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


def doinit():
    """ This method is called from __init__.py """
    print "initializing linklist category type ..."
    register_category_type(BlogCategoryType)

