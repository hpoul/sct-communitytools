# Create your views here.
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.db.models import Q
from django.template.context import RequestContext
from django import newforms as forms
from django.dispatch import dispatcher

from datetime import datetime

from sphene.community import PermissionDenied
from sphene.community import sphutils
from sphene.community.middleware import get_current_user, get_current_sphdata
from sphene.community.sphutils import get_fullusername, format_date
from sphene.sphboard import boardforms
from sphene.sphboard.models import Category, Post, PostAnnotation, ThreadInformation, POST_STATUSES, Poll, PollChoice, PollVoters, POST_MARKUP_CHOICES, THREAD_TYPE_MOVED, THREAD_TYPE_DEFAULT
from sphene.sphboard.renderers import describe_render_choices

        

def showCategory(request, group = None, category_id = None, showType = None):
    args = {
        'group__isnull': True,
        'parent__isnull': True,
        }
    categoryObject = None
    
    sphdata = get_current_sphdata()
    
    if category_id != None and category_id != '0':
        args['parent__isnull'] = False
        args['parent'] = category_id
        categoryObject = get_object_or_404(Category, pk = category_id)
        if not categoryObject.has_view_permission( request.user ):
            raise PermissionDenied()
        categoryObject.touch(request.session, request.user)
        if sphdata != None: sphdata['subtitle'] = categoryObject.name
        
    if group != None:
        args['group__isnull'] = False
        args['group'] = group

    if showType == 'threads':
        categories = []
    else:
        if 'group' in args:
            categories = Category.sph_objects.filter_for_group( args['group'] )
            if 'parent' in args:
                categories = categories.filter( parent = category_id )
            else:
                categories = categories.filter( parent__isnull = True )
        else:
            categories = Category.objects.filter( **args )
    
    context = { 'rootCategories': categories,
                'category': categoryObject,
                'allowPostThread': categoryObject and categoryObject.allowPostThread( request.user ),
                'category_id': category_id, }
    templateName = 'sphene/sphboard/listCategories.html'
    if categoryObject == None:
        if showType != 'threads':
            return render_to_response( templateName, context,
                                       context_instance = RequestContext(request) )
        
        ## Show the latest threads from all categories.
        all_categories = Category.objects.filter( group = group )
        allowed_categories = ()
        for category in all_categories:
            if category.has_view_permission( request.user ):
                allowed_categories += (category.id,)
        
        if group != None: thread_args = { 'category__group': group }
        else: thread_args = { 'category__group__isnull': True }
        #thread_args[ 'thread__isnull'] = True
        thread_args[ 'category__id__in'] = allowed_categories
        context['isShowLatest'] = True
        thread_list = ThreadInformation.objects.filter( **thread_args )
    else:
        thread_list = categoryObject.get_thread_list()

    #thread_list = thread_list.extra( select = { 'latest_postdate': 'SELECT MAX(postdate) FROM sphboard_post AS postinthread WHERE postinthread.thread_id = sphboard_post.id OR postinthread.id = sphboard_post.id', 'is_sticky': 'status & %d' % POST_STATUSES['sticky'] } )
    if showType != 'threads':
        thread_list = thread_list.order_by( '-sticky_value', '-thread_latest_postdate' )
    else:
        thread_list = thread_list.order_by( '-thread_latest_postdate' )

    res =  object_list( request = request,
                        queryset = thread_list,
                        template_name = templateName,
                        extra_context = context,
                        template_object_name = 'thread',
                        allow_empty = True,
                        paginate_by = 10,
                        )
    
    res.sph_lastmodified = True
    return res

def showThread(request, thread_id, group = None):
    thread = Post.objects.filter( pk = thread_id ).get()
    if not thread.category.has_view_permission(request.user):
        raise PermissionDenied()
    thread.viewed( request.session, request.user )
    #thread = get_object_or_404(Post, pk = thread_id )

    sphdata = get_current_sphdata()
    if sphdata != None: sphdata['subtitle'] = thread.subject
    
    res =  object_list( request = request,
                        #queryset = Post.objects.filter( Q( pk = thread_id ) | Q( thread = thread ) ).order_by('postdate'),
                        queryset = thread.get_all_posts().order_by('postdate'),
                        allow_empty = True,
                        template_name = 'sphene/sphboard/showThread.html',
                        extra_context = { 'thread': thread,
                                          'allowPosting': thread.allowPosting( request.user ),
                                          'postSubject': 'Re: ' + thread.subject,
                                          },
                        template_object_name = 'post',
                        )

    res.sph_lastmodified = thread.get_latest_post().postdate
    return res

def options(request, thread_id, group = None):
    thread = Post.objects.get( pk = thread_id )

    if request['cmd'] == 'makeSticky':
        thread.set_sticky(True)
    elif request['cmd'] == 'removeSticky':
        thread.set_sticky(False)
    elif request['cmd'] == 'toggleClosed':
        thread.set_closed(not thread.is_closed())
    elif request['cmd'] == 'modifytags':
        from tagging.models import Tag
        Tag.objects.update_tags( thread.get_threadinformation(), [request.POST['tags'], ] )

    thread.save()
    
    return HttpResponseRedirect( '../../thread/%s/' % thread.id )

class PostForm(forms.Form):
    subject = forms.CharField()
    body = forms.CharField( widget = forms.Textarea( attrs = { 'rows': 10, 'cols': 80 } ),
                            help_text = describe_render_choices(), )
    markup = forms.CharField( widget = forms.Select( choices = POST_MARKUP_CHOICES, ) )
    captcha = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
                                    help_text = 'Please enter the result of the above calculation.',
                                    )

    def __init__(self, *args, **kwargs):
        super(PostForm, self).__init__(*args, **kwargs)
        if not sphutils.has_captcha_support() or get_current_user().is_authenticated():
            del self.fields['captcha']
        if len( POST_MARKUP_CHOICES ) == 1:
            del self.fields['markup']

class PostPollForm(forms.Form):
    question = forms.CharField()
    answers = forms.CharField( label = 'Answers (1 per line)',
                               widget = forms.Textarea( attrs = { 'rows': 5, 'cols': 80 } ) )
    choicesPerUser = forms.IntegerField( label = 'Allowed Choices per User',
                                         help_text = 'Enter how many answers a user can select.',
                                         min_value = 1,
                                         max_value = 100,
                                         initial = 1, )


def post(request, group = None, category_id = None, post_id = None):
    if 'type' in request.REQUEST and request.REQUEST['type'] == 'preview':
        previewpost = Post( body = request.REQUEST['body'],
                            markup = request.REQUEST.get('markup', None), )
        return HttpResponse( previewpost.body_escaped() )

    
    post = None

    if post_id:
        post = get_object_or_404(Post, pk = post_id)
        if not post.allowEditing():
            raise PermissionDenied()
    
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
            data = postForm.cleaned_data

            if post:
                newpost = post
                newpost.subject = data['subject']
                newpost.body = data['body']
                newpost.body += "\n\n--- Last Edited by %s at %s ---" % ( get_fullusername( request.user ), format_date( datetime.today()) )
            else:
                newpost = Post( category = category,
                                subject = data['subject'],
                                body = data['body'],
                                author = request.user,
                                thread = thread,
                                )
            if 'markup' in data:
                newpost.markup = data['markup']
                
            elif len( POST_MARKUP_CHOICES ) == 1:
                newpost.markup = POST_MARKUP_CHOICES[0][0]
                
            newpost.save()


            # Creating monitor
            if request.POST.get( 'addmonitor', False ):
                newpost.toggle_monitor()


            if 'createpoll' in request.POST and request.POST['createpoll'] == '1':
                newpost.set_poll( True );
                newpost.save()

                # Creating poll...
                polldata = pollForm.cleaned_data
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
                if request.user.is_authenticated():
                    request.user.message_set.create( message = "Vote created successfully." )

            if request.user.is_authenticated():
                if post:
                    request.user.message_set.create( message = "Post edited successfully." )
                else:
                    request.user.message_set.create( message = "Post created successfully." )
            if thread == None: thread = newpost
            return HttpResponseRedirect( thread.get_absolute_url() )

    else:
        postForm = PostForm( )
        pollForm = PostPollForm()

    if post:
        postForm.fields['subject'].initial = post.subject
        postForm.fields['body'].initial = post.body
        if 'markup' in postForm.fields:
            postForm.fields['markup'].initial = post.markup
        context['post'] = post
        context['thread'] = post.thread or post
    elif 'quote' in request.REQUEST:
        quotepost = Post.objects.get( pk = request.REQUEST['quote'] )
        postForm.fields['subject'].initial = 'Re: %s' % thread.subject
        if quotepost.author == None:
            username = 'anonymous'
        else:
            username = quotepost.author.username
        postForm.fields['body'].initial = '[quote=%s;%s]\n%s\n[/quote]\n' % (username, quotepost.id, quotepost.body)
    elif thread:
        postForm.fields['subject'].initial = 'Re: %s' % thread.subject
    context['form'] = postForm
    context['pollform'] = pollForm
    if 'createpoll' in request.REQUEST:
        context['createpoll'] = request.REQUEST['createpoll']

    return render_to_response( "sphene/sphboard/post.html", context,
                               context_instance = RequestContext(request) )


class AnnotateForm(forms.Form):
    body = forms.CharField( widget = forms.Textarea( attrs = { 'rows': 10,
                                                               'cols': 80, }, ),
                                                     help_text = describe_render_choices(), )
    markup = forms.CharField( widget = forms.Select( choices = POST_MARKUP_CHOICES, ) )
    hide_post = forms.BooleanField( required = False )

    def __init__(self, *args, **kwargs):
        super(AnnotateForm, self).__init__(*args, **kwargs)
        if len( POST_MARKUP_CHOICES ) == 1:
            del self.fields['markup']

    def clean(self):
        if 'markup' not in self.cleaned_data and len( POST_MARKUP_CHOICES ):
            self.cleaned_data['markup'] = POST_MARKUP_CHOICES[0][0]
            
        return self.cleaned_data

def annotate(request, group, post_id):
    post = Post.objects.get( pk = post_id )
    thread = post.get_thread()
    if not thread.allow_moving():
        raise PermissionDenied()

    annotation = None
    if post.is_annotated():
        try:
            annotation = post.annotation.get()
        except PostAnnotation.DoesNotExist:
            # Ignore for now ..
            pass


    if request.method == 'POST':
        form = AnnotateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if annotation is None:
                annotation = PostAnnotation( post = post, )
            annotation.body = data['body']
            annotation.hide_post = data['hide_post']
            annotation.markup = data['markup']
            annotation.save()
            request.user.message_set.create( message = "Annotated a users post." )
            return HttpResponseRedirect( post.get_absolute_url() )
        
    else:
        form = AnnotateForm()

    if annotation is not None:
        form.fields['body'].initial = annotation.body
        form.fields['hide_post'].initial = annotation.hide_post
        if 'markup' in form.fields:
            form.fields['markup'].initial = annotation.markup

    
    return render_to_response( "sphene/sphboard/annotate.html",
                               { 'thread': thread,
                                 'post': post,
                                 'form': form,
                                 },
                               context_instance = RequestContext(request) )


class MoveForm(forms.Form):
    """
    A basic form which allows a user to select a target
    category.

    This should not be used allown, but in stead use
    MoveAndAnnotateForm
    """
    category = boardforms.SelectCategoryField(help_text = u'Select target category')


class MoveAndAnnotateForm(MoveForm, AnnotateForm):

    
    def __init__(self, *args, **kwargs):
        super(MoveAndAnnotateForm, self).__init__(*args, **kwargs)

        del self.fields['hide_post']

        self.fields['body'].help_text = 'Please describe why this thread had to be moved. ' + self.fields['body'].help_text


def move(request, group, thread_id):
    thread = get_object_or_404(Post, pk = thread_id)
    if not thread.allow_moving():
        raise PermissionDenied()

    annotation = None
    if thread.is_annotated():
        try:
            annotation = thread.annotation.get()
        except PostAnnotation.DoesNotExist:
            # Ignore for now ..
            pass
    if request.method == 'POST':
        form = MoveAndAnnotateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            newcategory = data['category']

            threadinfo = thread.get_threadinformation()
            threadinfo.thread_type = THREAD_TYPE_MOVED
            threadinfo.save()

            try:
                newthreadinfo = ThreadInformation.objects.get( root_post = thread,
                                                               category = newcategory,
                                                               thread_type = THREAD_TYPE_MOVED )
            except ThreadInformation.DoesNotExist:
                newthreadinfo = ThreadInformation( root_post = thread,
                                                   category = newcategory, )

            newthreadinfo.thread_type = THREAD_TYPE_DEFAULT
            newthreadinfo.update_cache()
            newthreadinfo.save()

            thread.set_annotated(True)

            if annotation is None:
                annotation = PostAnnotation( post = thread, )
            annotation.body = data['body']
            annotation.hide_post = False
            annotation.markup = data['markup']
            annotation.save()

            thread.category = newcategory
            thread.save()

            request.user.message_set.create( message = "Moved thread into new category." )

            return HttpResponseRedirect( thread.get_absolute_url() )
        
    else:
        form = MoveAndAnnotateForm()

    if POST_MARKUP_CHOICES[0][0] == 'bbcode':
        category_name = '[url=%s]%s[/url].' % (thread.category.get_absolute_url(), thread.category.name)
    else:
        category_name = thread.category.name
    form.fields['body'].initial = 'This thread was moved from the category %s' % category_name

    return render_to_response( "sphene/sphboard/move.html",
                               { 'thread': thread,
                                 'form': form,
                                 },
                               context_instance = RequestContext(request))


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

def toggle_monitor(request, group, monitortype, object_id):
    redirectview = 'show'
    obj = None
    if monitortype == 'group':
        obj = group
        object_id = 0
    elif monitortype == 'category':
        obj = Category.objects.get( pk = object_id )
    elif monitortype == 'thread':
        obj = Post.objects.get( pk = object_id )
        redirectview = 'thread'

    if obj.toggle_monitor():
        request.user.message_set.create( message = "Successfully created email notification monitor." )
    else:
        request.user.message_set.create( message = "Removed email notification monitor." )

    return HttpResponseRedirect( '../../%s/%s/' % (redirectview, object_id) )


def catchup(request, group, category_id):
    category = get_object_or_404(Category, pk = category_id )
    category.catchup(request.session, request.user)
    req = HttpResponseRedirect( '../../show/%s/' % category_id )
    req.sph_lastmodified = True
    return req



