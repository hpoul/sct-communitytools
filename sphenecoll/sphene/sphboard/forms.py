"""
Collection of forms for the board application


i have created this module quite late, so most forms are still
in views.py
"""

from django import forms

from sphene.sphboard.models import Poll, PollChoice, Post

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

