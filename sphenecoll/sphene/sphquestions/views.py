
from django.http import Http404, HttpResponseRedirect, HttpResponse


from sphene.community import PermissionDenied
from sphene.community.middleware import get_current_user

from sphene.sphboard.models import Post

from sphene.sphquestions.models import AnswerVoting

def votereply(request, group, reply_id):
    reply = Post.objects.get( pk = reply_id )
    question = reply.get_thread()
    qext = question.sphquestions_ext.get()

    if reply.author == request.user and question.author != reply.author:
        # Users are not allowed to vote for their own replies.
        raise PermissionDenied()

    AnswerVoting(user = request.user,
                 answer = reply,
                 question = qext,
                 rating = 5).save()

    answered = 1
    if request.user == question.author:
        answered = 3

    if qext.answered < answered:
        qext.answered = answered
        qext.save()

    return HttpResponseRedirect(reply.get_absolute_url())

