# Create your views here.
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.db.models import Q
from django.template.context import RequestContext
from django import newforms as forms

from sphene.sphboard.models import Category, Post, POST_STATUSES, Poll, PollChoice, PollVoters

class SpheneModelInitializer:
    def __init__(self, request):
        self.request = request

    def init_model(self, model):
        model.do_init( self, self.request.session, self.request.user )
        

def showCategory(request, group = None, category_id = None, showType = None):
    args = {
        'group__isnull': True,
        'parent__isnull': True,
        }
    categoryObject = None
    if category_id != None and category_id != '0':
        args['parent__isnull'] = False
        args['parent'] = category_id
        categoryObject = Category.objects.get( pk = category_id )
    if group != None:
        args['group__isnull'] = False
        args['group'] = group

    if showType == 'threads':
        categories = []
    else:
        categories = Category.objects.filter( **args ).add_initializer( SpheneModelInitializer(request) )
    
    context = { 'rootCategories': categories,
                'category': categoryObject,
                'allowPostThread': categoryObject and categoryObject.allowPostThread( request.user ),
                'category_id': category_id, }
    templateName = 'sphene/sphboard/listCategories.html'
    if categoryObject == None:
        if showType != 'threads':
            return render_to_response( templateName, context,
                                       context_instance = RequestContext(request) )
        if group != None: thread_args = { 'category__group': group }
        else: thread_args = { 'category__group__isnull': True }
        thread_args[ 'thread__isnull'] = True
        context['isShowLatest'] = True
        thread_list = Post.objects.filter( **thread_args )
    else:
        thread_list = categoryObject.thread_list()

    thread_list = thread_list.extra( select = { 'latest_postdate': 'SELECT MAX(postdate) FROM sphboard_post AS postinthread WHERE postinthread.thread_id = sphboard_post.id OR postinthread.id = sphboard_post.id', 'is_sticky': 'status & %d' % POST_STATUSES['sticky'] } ).add_initializer( SpheneModelInitializer(request) )
    if showType != 'threads':
        thread_list = thread_list.order_by( '-is_sticky', '-latest_postdate' )
    else:
        thread_list = thread_list.order_by( '-latest_postdate' )

    return object_list( request = request,
                        queryset = thread_list,
                        template_name = templateName,
                        extra_context = context,
                        template_object_name = 'thread',
                        allow_empty = True,
                        paginate_by = 10,
                        )

def showThread(request, thread_id, group = None):
    thread = Post.objects.filter( pk = thread_id ).add_initializer( SpheneModelInitializer( request ) ).get()
    thread.touch( request.session, request.user )
    #thread = get_object_or_404(Post, pk = thread_id )
    return object_list( request = request,
                        #queryset = Post.objects.filter( Q( pk = thread_id ) | Q( thread = thread ) ).order_by('postdate'),
                        queryset = thread.allPosts().order_by('postdate').add_initializer( SpheneModelInitializer( request ) ),
                        allow_empty = True,
                        template_name = 'sphene/sphboard/showThread.html',
                        extra_context = { 'thread': thread,
                                          'allowPosting': thread.allowPosting( request.user ),
                                          'postSubject': 'Re: ' + thread.subject,
                                          },
                        template_object_name = 'post',
                        )

def options(request, thread_id, group = None):
    thread = Post.objects.get( pk = thread_id )

    if request['cmd'] == 'makeSticky':
        thread.set_sticky(True)
    elif request['cmd'] == 'removeSticky':
        thread.set_sticky(False)

    thread.save()
    
    return HttpResponseRedirect( '../../thread/%s/' % thread.id )

class PostForm(forms.Form):
    subject = forms.CharField()
    body = forms.CharField( widget = forms.Textarea( attrs = { 'rows': 10, 'cols': 80 } ) )

class PostPollForm(forms.Form):
    question = forms.CharField()
    answers = forms.CharField( label = 'Answers (1 per line)',
                               widget = forms.Textarea( attrs = { 'rows': 5, 'cols': 80 } ) )
    choicesPerUser = forms.IntegerField( label = 'Allowed Choices per User',
                                         help_text = 'Enter how many answers a user can select.',
                                         min_value = 1,
                                         max_value = 100,
                                         initial = 1, )


def post(request, group = None, category_id = None):
    thread = None
    category = None
    context = { }
    if 'thread' in request.REQUEST:
        thread = get_object_or_404(Post, pk = request.REQUEST['thread'])
        category = thread.category
        context['thread'] = thread
    else:
        category = get_object_or_404(Category, pk = category_id)
    if not category.allowPostThread( request.user ): raise Http404;
    context['category'] = category

    if request.method == 'POST':
        postForm = PostForm(request.POST)
        pollForm = PostPollForm(request.POST)
        if postForm.is_valid() and 'createpoll' not in request.POST or pollForm.is_valid():
            data = postForm.clean_data
    
            newpost = Post( category = category,
                            subject = data['subject'],
                            body = data['body'],
                            author = request.user,
                            thread = thread,
                            )
            newpost.save()

            if 'createpoll' in request.POST and request.POST['createpoll'] == '1':
                newpost.set_poll( True );
                newpost.save()
                # Creating poll...
                polldata = pollForm.clean_data
                newpoll = Poll( post = newpost,
                                question = polldata['question'],
                                choices_per_user = polldata['choicesPerUser'])
                newpoll.save()

                choices = polldata['answers'].splitlines()
                for choice in choices:
                    pollchoice = PollChoice( poll = newpoll,
                                             choice = choice,
                                             count = 0, )
                    pollchoice.save()
                request.user.message_set.create( message = "Vote created successfully." )
                
            
            request.user.message_set.create( message = "Post created successfully." )
            if thread == None: thread = newpost
            return HttpResponseRedirect( '../../thread/%s/' % thread.id )

    else:
        postForm = PostForm()
        pollForm = PostPollForm()

    if thread:
        postForm.fields['subject'] = forms.CharField()
        postForm.fields['subject'].initial = 'Re: %s' % thread.subject
    context['form'] = postForm
    context['pollform'] = pollForm
    if 'createpoll' in request.REQUEST:
        context['createpoll'] = request.REQUEST['createpoll']

    return render_to_response( "sphene/sphboard/post.html", context,
                               context_instance = RequestContext(request) )


def vote(request, group = None, thread_id = None):
    thread = get_object_or_404(Post, pk = thread_id)

    poll = thread.poll()
    if poll.has_voted(request.user):
        request.attributes['voteerror'] = "You have already voted."
        return showThread(request, thread_id, group)

    if not 'pollchoice' in request.REQUEST or len( request.REQUEST['pollchoice'] ) < 1:
        request.attributes['voteerror'] = "Please select at least one answer."
        return showThread(request, thread_id, group)

    pollchoices = request.REQUEST.getlist('pollchoice')
    
    if poll.choices_per_user < len( pollchoices ):
        request.attributes['voteerror'] = "Please only select %d answers." % poll.choices_per_user
        return showThread(request, thread_id, group)

    if len( pollchoices ) > 1 and '0' in pollchoices:
        request.attributes['voteerror'] = "You cannot abstain from voting and at the same time select a valid answer."
        return showThread(request, thread_id, group)

    for pollchoice in pollchoices:
        if pollchoice == '0': choice = None
        else:
            try:
                choice = poll.pollchoice_set.get( pk = pollchoice )
            except PollChoice.DoesNotExist:
                request.attributes['voteerror'] = "You've selected an invalid choice."
                return showThread(request, thread_id, group)
            choice.count = choice.count + 1
            choice.save()
        voter = PollVoters( poll = poll,
                            choice = choice,
                            user = request.user, )
        voter.save()
        request.user.message_set.create( message = choice and "Voted for '%s'." % choice.choice or "You selected to abstain from voting" )
    

    return HttpResponseRedirect( '../../thread/%s/' % thread.id )
