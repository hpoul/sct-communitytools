"""
Collection of forms for the board application


i have created this module quite late, so most forms are still
in views.py
"""

from django import forms
from django.utils.translation import string_concat
from django.utils.translation import ugettext_lazy as _

from sphene.community import sphutils
from sphene.community.middleware import get_current_user

from sphene.sphboard.models import Poll, PollChoice, Post
from sphene.sphboard.renderers import describe_render_choices
from sphene.sphboard.models import POST_MARKUP_CHOICES, PostAttachment
from sphene.sphboard import boardforms
from sphene.community.widgets import SPHFileWidget


class PollForm(forms.ModelForm):

    class Meta:
        model = Poll


class PollChoiceForm(forms.ModelForm):

    class Meta:
        model = PollChoice
        exclude = ('count',)


class PostModelForm(forms.ModelForm):
    """
    a new version of the sphene.sphboard.views.PostForm class ..
    still in development, not usable yet.
    """

    def __init__(self, *args, **kwargs):
        super(PostModelForm, self).__init__(*args, **kwargs)
        #if not sphutils.has_captcha_support() or get_current_user().is_authenticated():
        #    del self.fields['captcha']

        # if there is no choice for 'markup' .. don't show it.
        # (we compare to len == 2 because the first option is always '----------')
        if len( self.fields['markup'].widget.choices ) == 2: #POST_MARKUP_CHOICES ) == 1:
            del self.fields['markup']


    class Meta:
        model = Post


class PostForm(forms.Form):
    subject = forms.CharField( label = _(u"Subject" ) )
    body = forms.CharField( label = _(u"Body"),
                            widget = forms.Textarea( attrs = { 'rows': 10, 'cols': 70 } ),
                            help_text = describe_render_choices(), )
    markup = forms.CharField( label=_('Markup'),
                              widget = forms.Select( choices = POST_MARKUP_CHOICES, ) )
    captcha = sphutils.CaptchaField(label=_('Captcha'),
                                    widget=sphutils.CaptchaWidget,
                                    help_text = _(u'Please enter the result of the above calculation.'),
                                    )

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        if not sphutils.has_captcha_support() or get_current_user().is_authenticated():
            del self.fields['captcha']
        if len( POST_MARKUP_CHOICES ) == 1:
            del self.fields['markup']

    def init_for_category_type(self, category_type, post):
        """
        Called after initialization with the category type instance.

        Arguments:
        category_type: the category_type instance of the category.
        post: the post which is edited (if any)
        """
        pass


class PostPollForm(forms.Form):
    question = forms.CharField( label = _( u'Question' ) )
    answers = forms.CharField( label = _( u'Answers (1 per line)' ),
                               widget = forms.Textarea( attrs = { 'rows': 5, 'cols': 80 } ) )
    choicesPerUser = forms.IntegerField( label = _(u'Allowed Choices per User'),
                                         help_text = _(u'Enter how many answers a user can select.'),
                                         min_value = 1,
                                         max_value = 100,
                                         initial = 1, )


class PostAttachmentForm(forms.ModelForm):
    fileupload = forms.FileField(label= _('File'), widget=SPHFileWidget)

    class Meta:
        model = PostAttachment
        fields = ('fileupload',)


class AnnotateForm(forms.Form):
    body = forms.CharField( label=_(u'Body'), widget = forms.Textarea( attrs = { 'rows': 10,
                                                               'cols': 80, }, ),
                                                     help_text = describe_render_choices(), )
    markup = forms.CharField( label=_('Markup'),
                              widget = forms.Select( choices = POST_MARKUP_CHOICES, ) )
    hide_post = forms.BooleanField( label=_('Hide Post'), required = False )

    def __init__(self, *args, **kwargs):
        super(AnnotateForm, self).__init__(*args, **kwargs)
        if len( POST_MARKUP_CHOICES ) == 1:
            del self.fields['markup']

    def clean(self):
        if 'markup' not in self.cleaned_data and len( POST_MARKUP_CHOICES ):
            self.cleaned_data['markup'] = POST_MARKUP_CHOICES[0][0]

        return self.cleaned_data


class MoveForm(forms.Form):
    """
    A basic form which allows a user to select a target
    category.

    This should not be used allown, but in stead use
    MoveAndAnnotateForm
    """
    category = boardforms.SelectCategoryField(label = _(u'Category'),
                                              help_text = _(u'Select target category'))
    info_link = forms.BooleanField(label = _('Information link'),
                                   initial = True,
                                   required = False,
                                   help_text=_('If checked then information about moved thread will be left in the current category'))


class MoveAndAnnotateForm(MoveForm, AnnotateForm):
    def __init__(self, *args, **kwargs):
        super(MoveAndAnnotateForm, self).__init__(*args, **kwargs)

        del self.fields['hide_post']

        self.fields['body'].help_text = string_concat(_(u'Please describe why this thread had to be moved.'), ' ', self.fields['body'].help_text)


class MovePostForm(AnnotateForm):
    move_all_posts = forms.BooleanField(label = _('Move all post after this post'),
                                        initial = False,
                                        required = False,
                                        help_text=_('If checked then all posts following this post will be also moved'))

    def __init__(self, *args, **kwargs):
        super(MovePostForm, self).__init__(*args, **kwargs)
        del self.fields['hide_post']
        self.fields['body'].help_text = string_concat(_(u'Please describe why this post had to be moved.'), ' ', self.fields['body'].help_text)
