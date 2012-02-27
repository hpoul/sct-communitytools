
from django import forms
from django.utils.translation import ugettext_lazy, ugettext


from sphene.sphboard.views import PostForm
from sphene.sphboard.categorytypes import DefaultCategoryType


from sphene.sphquestions.models import QuestionPostExtension, AnswerVoting

class QuestionPostForm(PostForm):
    is_question = forms.BooleanField(label = ugettext_lazy('Mark as Question'),
                                     help_text = ugettext_lazy('When posting a question you are able to mark the relevance of posts and wether a reply has answered your question.'),
                                     required = False,
                                     initial = True)



class QuestionCategoryType(DefaultCategoryType):
    name = 'sphquestion'
    label = ugettext_lazy('Questions & Answers')

    def get_post_form_class(self, replypost, editpost):
        if replypost is not None and \
                (editpost is None or editpost.thread is not None):
            # If we are posting a reply, use the default PostForm
            return PostForm
        return QuestionPostForm


    def save_post(self, newpost, data):
        super(QuestionCategoryType, self).save_post(newpost, data)
        
        if newpost.thread is not None:
            return
        ext,created = QuestionPostExtension.objects.get_or_create( \
            post = newpost,
            defaults = { 'is_question': data['is_question'],
                         'answered': 0, })
        if not created:
            ext.is_question = data['is_question']
            ext.save()


    def get_threadlist_template(self):
        """
        customized thread list which adds question mark icons.
        """
        return 'sphene/sphquestions/thread_list.html'

    def get_show_thread_template(self):
        return 'sphene/sphquestions/show_thread.html'




