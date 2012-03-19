from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe


from sphene.community.middleware import get_current_user, get_current_sphdata, get_current_urlconf
from sphene.community.sphutils import sph_reverse
from sphene.community.models import Tag, TagLabel, TaggedItem, tag_set_labels, tag_get_labels
from sphene.community.fields import TagField
from sphene.community.widgets import TagWidget

from sphene.sphboard.models import Post
from sphene.sphboard.views import PostForm
from sphene.sphboard.categorytyperegistry import CategoryType, register_category_type
from sphene.sphblog.models import BlogPostExtension, BLOG_POST_STATUS_CHOICES, BlogCategoryConfig
from sphene.sphblog.utils import slugify


class BlogPostForm(PostForm):
    slug = forms.CharField(required = False,
                           help_text = "Optionally define a slug for this blog post. Otherwise it will be filled automatically.")
    status = forms.ChoiceField(choices = BLOG_POST_STATUS_CHOICES,
                               initial = 2)
    tags = TagField(model = Post, required = False)

    def clean_slug(self):
        if not 'subject' in self.cleaned_data:
            raise forms.ValidationError( 'No subject to generate slug.' )
        slug = self.cleaned_data['slug']
        if slug == '':
            slug = slugify(self.cleaned_data['subject'], model=BlogPostExtension)
        else:
            slug = slugify(slug, model=BlogPostExtension, pk=self.__ext_id)
        return slug

    def init_for_category_type(self, category_type, post):
        self.__ext_id = None
        super(BlogPostForm, self).init_for_category_type(category_type, post)
        if post:
            try:
                ext = post.blogpostextension_set.get()
                self.__ext_id = ext.id
                self.fields['tags'].initial = tag_get_labels(post)
                self.fields['slug'].initial = ext.slug
                self.fields['status'].initial = ext.status
            except BlogPostExtension.DoesNotExist:
                # This can happen after post was created for
                # attaching a file.. which wouldn't create a BlogPostExtension.
                pass


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

        tag_set_labels( newpost, data['tags'] )

        if newpost.is_new_post:
            try:
                config = BlogCategoryConfig.objects.get( \
                    category = self.category)

                if config.enable_googleblogping:
                    # If enabled, ping google blogsearch.
                    import urllib
                    url = self.category.group.get_baseurl()
                    blog_feed_url = reverse('sphblog-feeds', urlconf=get_current_urlconf(), kwargs = { 'category_id': self.category.id })
                    pingurl = 'http://blogsearch.google.com/ping?%s' % \
                        urllib.urlencode( \
                        { 'name': self.category.name,
                          'url': ''.join((url, self.category.get_absolute_url()),),
                          'changesURL': ''.join((url, blog_feed_url),) } )
                    urllib.urlopen( pingurl )

            except BlogCategoryConfig.DoesNotExist:
                pass
                


    def get_absolute_url_for_post(self, post):
        return post.get_thread().blogpostextension_set.get().get_absolute_url()

    def append_edit_message_to_post(self, post):
        return post.thread is not None

    def get_show_thread_template(self):
        return 'sphene/sphblog/show_blogentry_layer.html'

    def get_absolute_url_for_category(self):
        try:
            blog_url = sph_reverse('sphblog_category_index_slug', kwargs = { 'category_slug': self.category.slug })
            return blog_url
        except Exception, e:
            #print "err.. argl %s" % str(e)
            return None



class HiddenBlogCategoryType(BlogCategoryType):
    name = "sphbloghidden"

    label = "Blog Category hidden from forum overviews"

    def is_displayed(self):
        return False

