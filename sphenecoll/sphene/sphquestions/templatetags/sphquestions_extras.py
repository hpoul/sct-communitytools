

from django import template
from django.conf import settings

from sphene.community.middleware import get_current_user

from sphene.sphquestions.models import AnswerVoting

register = template.Library()



@register.inclusion_tag('sphene/sphquestions/_answervoting.html')
def sphquestions_answervoting(qext, reply):
    user = get_current_user()
    if not qext or not qext.is_question or reply.thread is None:
        return { 'hidden': True }

    # don't diplay answer voting if user is not logged in
    # or if the post is not a question or not a reply.
    if user is None \
            or not user.is_authenticated() \
            or reply.author == user:
        allowvoting = False
    else:
        allowvoting = True

    question = reply.thread
    votes = AnswerVoting.objects.filter( answer = reply )
    uservoted = False
    authorvoted = False
    for vote in votes:
        if vote.user == user:
            uservoted = True
            allowvoting = False
        if vote.user == question.author:
            authorvoted = True
    
    return { 'qext'       : qext,
             'post'       : reply,
             'user'       : user,
             'uservoted'  : uservoted,
             'authorvoted': authorvoted,
             'votecount'  : len(votes),
             'MEDIA_URL'  : settings.MEDIA_URL,
             'allowvoting': allowvoting,
             }


