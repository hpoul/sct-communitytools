"""
Collection of forms for the board application


i have created this module quite late, so most forms are still
in views.py
"""

from django import newforms as forms

from sphene.sphboard.models import Poll, PollChoice

class PollForm(forms.ModelForm):

    class Meta:
        model = Poll


class PollChoiceForm(forms.ModelForm):

    class Meta:
        model = PollChoice
        exclude = ('count',)

