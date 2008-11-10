

from django.db import models
from django.contrib.auth.models import User


from sphene.community.middleware import get_current_group

from sphene.sphboard.models import Post, Category


class QuestionPostExtensionManager(models.Manager):
    def filter_unanswered_questions(self, category_ids = None):
        """
        Returns a query set for the latest unanswered questions.

        category_ids: a list of category ids, or None to take all
        of the current group.
        """
        categories = Category.objects.filter( \
            group = get_current_group(),
            category_type = 'sphquestion' )

        if category_ids is not None:
            # If category_ids was passed in, filter for them...
            categories.filter( id__in = category_ids )

        categories = filter(Category.has_view_permission, categories)

        category_ids = [category.id for category in categories]

        questions = self.filter( \
            post__thread__isnull = True,
            post__category__id__in = category_ids,
            answered = 0, ).order_by( 'post__postdate' )
        return questions


class QuestionPostExtension(models.Model):
    """
    Post extension which is used for threads as well as for replies.
    """
    post = models.ForeignKey(Post, unique=True, related_name = 'sphquestions_ext')

    is_question = models.BooleanField()
    # 0 = not answered
    # 1 = someone marked a reply as valid answer
    # 3 = author marked it as answered.
    answered = models.IntegerField()


    objects = QuestionPostExtensionManager()


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






