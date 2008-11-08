

from django.db import models
from django.contrib.auth.models import User


from sphene.sphboard.models import Post


class QuestionPostExtension(models.Model):
    """
    Post extension which is used for threads as well as for replies.
    """
    post = models.ForeignKey(Post, unique=True, related_name = 'sphquestions_ext')

    is_question = models.BooleanField()
    # 0 = not answered
    # 1 = someone marked a reply as valid answer
    # 2 = author marked it as answered.
    answered = models.IntegerField()


class AnswerVoting(models.Model):
    """
    n:m relation between questions and user who voted it useful.
    """
    user = models.ForeignKey(User)
    answer = models.ForeignKey(Post)

    question = models.ForeignKey(QuestionPostExtension)

    # rating from 0 to 5 (currently all votings are 5 point votings)
    rating = models.IntegerField()

    class Meta:
        unique_together = ( 'user', 'answer' )






