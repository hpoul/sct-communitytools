# Create your views here.
from django import forms, template
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.db.models import Q
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _, ugettext_lazy
from django.utils.translation import ugettext, string_concat
from django.core.urlresolvers import reverse


from datetime import datetime

from sphene.community import PermissionDenied
from sphene.community import sphutils
from sphene.community.sphutils import sph_reverse
from sphene.community.middleware import get_current_user, get_current_sphdata, get_current_urlconf
from sphene.community.sphutils import get_user_displayname, format_date, get_sph_setting, add_rss_feed, sph_render_to_response

from sphene.generic import advanced_object_list as objlist

from sphene.sphboard import boardforms
from sphene.sphboard.forms import PollForm, PollChoiceForm
from sphene.sphboard.models import Category, Post, PostAnnotation, ThreadInformation, POST_STATUSES, Poll, PollChoice, PollVoters, POST_MARKUP_CHOICES, THREAD_TYPE_MOVED, THREAD_TYPE_DEFAULT, PostAttachment, get_all_viewable_categories
from sphene.sphboard.renderers import describe_render_choices



def showCategory(request, group = None, category_id = None, showType = None):
    """
    displays either all root categories, or the contents of a category.
    the contents of a category could be other categories or forum threads.

    TODO: clean this mess up - sorry for everyone who trys to understand
    this function - this is is probably the oldest and ugliest in 
    the whole SCT source.
    """
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
        blog_feed_url = reverse('sphboard-feeds', urlconf=get_current_urlconf(), args = (), kwargs = { 'url': 'latest/2' })
        add_rss_feed( blog_feed_url, 'Latest Threads in %s RSS Feed' % categoryObject.name )

        if sphdata != None: sphdata['subtitle'] = categoryObject.name
        
    if group != None:
        args['group__isnull'] = False
        args['group'] = group

    if showType == 'threads':
        categories = []
    else:
        if 'group' in args:
            categories = Category.sph_objects.filter( group = args['group'] )#filter_for_group( args['group'] )
            if 'parent' in args:
                categories = categories.filter( parent = category_id )
            else:
                categories = categories.filter( parent__isnull = True )
            categories = [ category for category in categories if category.has_view_permission( request.user ) ]
        else:
            categories = Category.objects.filter( **args )
    
    context = { 'rootCategories': categories,
                'category': categoryObject,
                'allowPostThread': categoryObject and categoryObject.allowPostThread( request.user ),
                'category_id': category_id, }

    try:
        context['search_posts_url'] = sph_reverse('sphsearchboard_posts')
    except:
        pass

    templateName = 'sphene/sphboard/listCategories.html'
    if categoryObject == None:
        if showType != 'threads':
            return render_to_response( templateName, context,
                                       context_instance = RequestContext(request) )
        
        ## Show the latest threads from all categories.
        allowed_categories = get_all_viewable_categories( group, request.user )
        
        if group != None: thread_args = { 'category__group': group }
        else: thread_args = { 'category__group__isnull': True }
        #thread_args[ 'thread__isnull'] = True
        thread_args[ 'category__id__in'] = allowed_categories
        context['isShowLatest'] = True
        thread_list = ThreadInformation.objects.filter( **thread_args )
    else:
        category_type = categoryObject.get_category_type()
        templateName = category_type.get_threadlist_template()
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

def listThreads(request, group, category_id):
    """
    THIS IS JUST FOR TESTING PURPOSES FOR NOW !!!
    """
    from sphene.sphboard.lists import ThreadList
    # TODO check permissions
    queryset = ThreadInformation.objects.filter( category__pk = category_id )
    queryset = queryset.select_related( 'root_post', 'latest_post', )
    threadlist = ThreadList(objlist.QuerySetProvider(queryset),
                            object_name = ugettext_lazy( 'Threads' ),
                            prefix = 'threadlist',
                            session = request.session,
                            requestvars = request.GET,
                            defaultsortby = 'latestpostdate',
                            defaultsortorder = 'desc',
                            defaultcolconfig = ( 'newpost',
                                                 ( 'subject',
                                                   'author', ),
                                                 'views',
                                                 'posts', 
                                                 ( 'latestpostdate',
                                                   'latestpostauthor', ), ), )
    return sph_render_to_response( 'sphene/sphboard/new_list_threads.html',
                                   { 'threadlist': threadlist, })


def showThread(request, thread_id, group = None):
    thread = get_object_or_404(Post, pk = thread_id )
    if not thread.category.has_view_permission(request.user):
        raise PermissionDenied()
    thread.viewed( request.session, request.user )

    sphdata = get_current_sphdata()
    if sphdata != None: sphdata['subtitle'] = thread.subject

    category_type = thread.category.get_category_type()
    template_name = category_type.get_show_thread_template()
    
    res =  object_list( request = request,
                        #queryset = Post.objects.filter( Q( pk = thread_id ) | Q( thread = thread ) ).order_by('postdate'),
                        queryset = thread.get_all_posts().order_by('postdate'),
                        allow_empty = True,
                        template_name = template_name,
                        extra_context = { 'thread': thread,
                                          'allowPosting': thread.allowPosting( request.user ),
                                          'postSubject': 'Re: ' + thread.subject,
                                          'category_type': category_type,
                                          },
                        template_object_name = 'post',
                        paginate_by = get_sph_setting( 'board_post_paging' ),
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
    subject = forms.CharField( label = ugettext_lazy(u"Subject" ) )
    body = forms.CharField( label = ugettext_lazy(u"Body"),
                            widget = forms.Textarea( attrs = { 'rows': 10, 'cols': 70 } ),
                            help_text = describe_render_choices(), )
    markup = forms.CharField( widget = forms.Select( choices = POST_MARKUP_CHOICES, ) )
    captcha = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
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
    question = forms.CharField( label = ugettext_lazy( u'Question' ) )
    answers = forms.CharField( label = ugettext_lazy( u'Answers (1 per line)' ),
                               widget = forms.Textarea( attrs = { 'rows': 5, 'cols': 80 } ) )
    choicesPerUser = forms.IntegerField( label = _(u'Allowed Choices per User'),
                                         help_text = _(u'Enter how many answers a user can select.'),
                                         min_value = 1,
                                         max_value = 100,
                                         initial = 1, )

class PostAttachmentForm(forms.ModelForm):
    class Meta:
        model = PostAttachment
        fields = ('fileupload',)

def reply(*args, **kwargs):
    return post(*args, **kwargs)

def post(request, group = None, category_id = None, post_id = None, thread_id = None):
    if 'type' in request.REQUEST and request.REQUEST['type'] == 'preview':
        previewpost = Post( body = request.REQUEST['body'],
                            markup = request.REQUEST.get('markup', None), )
        return HttpResponse( unicode(previewpost.body_escaped()) )

    
    post = None
    thread = None
    category = None
    context = { }
    
    if post_id is None and 'post_id' in request.REQUEST:
        # if no post_id is given take it from the request.
        post_id = request.REQUEST['post_id']

    if post_id:
        try:
            post = Post.allobjects.get( pk = post_id )
        except Post.DoesNotExist:
            raise Http404

        if not post.allowEditing():
            raise PermissionDenied()
        thread = post.thread
    
    if 'thread' in request.REQUEST:
        thread_id = request.REQUEST['thread']

    if thread_id:
        try:
            thread = Post.allobjects.get( pk = thread_id )
        except Post.DoesNotExist:
            raise Http404

        category = thread.category
        context['thread'] = thread
        
        if not thread.allowPosting( request.user ):
            raise PermissionDenied()
    else:
        category = get_object_or_404(Category, pk = category_id)
        if not category.allowPostThread( request.user ):
            raise PermissionDenied()

    context['category'] = category

    category_type = category.get_category_type()
    MyPostForm = PostForm
    if category_type is not None:
        MyPostForm = category_type.get_post_form_class(thread, post)

    attachmentForm = None
    allow_attachments = get_sph_setting('board_allow_attachments')
    if request.method == 'POST':
        postForm = MyPostForm(request.POST)
        postForm.init_for_category_type(category_type, post)
        pollForm = PostPollForm(request.POST)

        create_post = True

        if allow_attachments:
            attachmentForm = PostAttachmentForm(request.POST,
                                                request.FILES,
                                                prefix = 'attachment')

            if 'cmd_addfile' in request.POST:
                create_post = False

            if attachmentForm.is_valid():
                attachment = attachmentForm.save(commit = False)
                if attachment.fileupload:
                    # Only save attachments if there was an upload...
                    # If the form is valid, store the attachment
                    if not post:
                        # if there is no post yet.. we need to create a draft
                        post = Post( category = category,
                                     author = request.user,
                                     thread = thread,
                                     is_hidden = 1,
                                     )
                        post.set_new( True )
                        post.save()

                    # Reference the post and save the attachment
                    attachment.post = post
                    attachment.save()


        if create_post \
                and postForm.is_valid() \
                and ('createpoll' not in request.POST \
                         or pollForm.is_valid()):
            data = postForm.cleaned_data

            if post:
                newpost = post
                newpost.subject = data['subject']
                newpost.body = data['body']
                # make post visible
                newpost.is_hidden = 0
                if not post.is_new() and category_type.append_edit_message_to_post(post):
                    newpost.body += "\n\n" + _(u'--- Last Edited by %(username)s at %(edit_date)s ---') % {'username':get_user_displayname( request.user ), 'edit_date':format_date( datetime.today())}
            else:
                user = request.user.is_authenticated() and request.user or None
                newpost = Post( category = category,
                                subject = data['subject'],
                                body = data['body'],
                                author = user,
                                thread = thread,
                                )
            if 'markup' in data:
                newpost.markup = data['markup']
                
            elif len( POST_MARKUP_CHOICES ) == 1:
                newpost.markup = POST_MARKUP_CHOICES[0][0]
                
            newpost.save()

            category_type.save_post( newpost, data )


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
                i=0
                for choice in choices:
                    pollchoice = PollChoice( poll = newpoll,
                                             choice = choice,
                                             count = 0,
                                             sortorder = i)
                    i+=1
                    pollchoice.save()
                if request.user.is_authenticated():
                    request.user.message_set.create( message = ugettext(u'Vote created successfully.') )

            if request.user.is_authenticated():
                if post:
                    request.user.message_set.create( message = ugettext(u'Post edited successfully.') )
                else:
                    request.user.message_set.create( message = ugettext(u'Post created successfully.') )
            if thread == None: thread = newpost
            return HttpResponseRedirect( newpost.get_absolute_url() )

    else:
        postForm = MyPostForm( )
        postForm.init_for_category_type(category_type, post)
        pollForm = PostPollForm()

        if allow_attachments:
            attachmentForm = PostAttachmentForm(prefix = 'attachment')

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

    # Only allow polls if this is a new _thread_ (not a reply)
    if (not thread and not post) or (post and post.is_new() and post.thread is None):
        context['pollform'] = pollForm
    context['attachmentForm'] = attachmentForm
    if 'createpoll' in request.REQUEST:
        context['createpoll'] = request.REQUEST['createpoll']

    res = render_to_response( "sphene/sphboard/post.html", context,
                              context_instance = RequestContext(request) )
    # Maybe the user is in the 'edit' form, which should not be cached.
    res.sph_lastmodified = True
    return res


def edit_poll(request, group, poll_id):
    poll = get_object_or_404(Poll, pk = poll_id)
    if not poll.allow_editing():
        raise PermissionDenied()

    postdata = None
    if request.method == 'POST':
        postdata = request.POST

    form = PollForm(postdata, instance = poll)
    choiceforms = [ PollChoiceForm( postdata,
                                    prefix = 'choice_%d' % choice.id,
                                    instance = choice,
                                    ) for choice in poll.pollchoice_set.all() ]

    if request.method == 'POST' and form.is_valid() \
            and not [ True for choiceform in choiceforms if not choiceform.is_valid() ]:
        form.save()
        for choiceform in choiceforms:
            choiceform.save()

        return HttpResponseRedirect(sph_reverse('sphene.sphboard.views.showThread',
                                                kwargs = { 'thread_id': poll.post.get_thread().id }))

    return sph_render_to_response('sphene/sphboard/edit_poll.html',
                                  { 'form': form,
                                    'choiceforms': choiceforms,
                                    })



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
            request.user.message_set.create( message = ugettext(u'Annotated a users post.') )
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
    category = boardforms.SelectCategoryField(help_text = _(u'Select target category'))


class MoveAndAnnotateForm(MoveForm, AnnotateForm):

    
    def __init__(self, *args, **kwargs):
        super(MoveAndAnnotateForm, self).__init__(*args, **kwargs)

        del self.fields['hide_post']

        self.fields['body'].help_text = string_concat(ugettext_lazy(u'Please describe why this thread had to be moved.'), ' ', self.fields['body'].help_text)


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

            request.user.message_set.create( message = ugettext(u'Moved thread into new category.') )

            return HttpResponseRedirect( thread.get_absolute_url() )
        
    else:
        form = MoveAndAnnotateForm()

    if POST_MARKUP_CHOICES[0][0] == 'bbcode':
        category_name = '[url=%s]%s[/url].' % (thread.category.get_absolute_url(), thread.category.name)
    else:
        category_name = thread.category.name
    form.fields['body'].initial = _(u'This thread was moved from the category %(category_name)s') % {'category_name':category_name}

    return render_to_response( "sphene/sphboard/move.html",
                               { 'thread': thread,
                                 'form': form,
                                 },
                               context_instance = RequestContext(request))


def vote(request, group = None, thread_id = None):
    thread = get_object_or_404(Post, pk = thread_id)

    poll = thread.poll()
    if poll.has_voted(request.user):
        request.attributes['voteerror'] = _(u'You have already voted.')
        return showThread(request, thread_id, group)

    if not 'pollchoice' in request.REQUEST or len( request.REQUEST['pollchoice'] ) < 1:
        request.attributes['voteerror'] = _(u'Please select at least one answer.')
        return showThread(request, thread_id, group)

    pollchoices = request.REQUEST.getlist('pollchoice')
    
    if poll.choices_per_user < len( pollchoices ):
        request.attributes['voteerror'] = _(u'Please only select %(choices)d answers.') % {'choices':poll.choices_per_user}
        return showThread(request, thread_id, group)

    if len( pollchoices ) > 1 and '0' in pollchoices:
        request.attributes['voteerror'] = _(u'You cannot abstain from voting and at the same time select a valid answer.')
        return showThread(request, thread_id, group)

    for pollchoice in pollchoices:
        if pollchoice == '0': choice = None
        else:
            try:
                choice = poll.pollchoice_set.get( pk = pollchoice )
            except PollChoice.DoesNotExist:
                request.attributes['voteerror'] = _(u"You've selected an invalid choice.")
                return showThread(request, thread_id, group)
            choice.count = choice.count + 1
            choice.save()
        voter = PollVoters( poll = poll,
                            choice = choice,
                            user = request.user, )
        voter.save()
        request.user.message_set.create( message = choice and ugettext(u"Voted for '%(choice)s'.") % {'choice': choice.choice} or ugettext(u'You selected to abstain from voting') )
    

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
        request.user.message_set.create( message = ugettext(u'Successfully created email notification monitor.') )
    else:
        request.user.message_set.create( message = ugettext(u'Removed email notification monitor.') )

    if 'next' in request.GET:
        return HttpResponseRedirect( request.GET['next'] )
    return HttpResponseRedirect( '../../%s/%s/' % (redirectview, object_id) )


def catchup(request, group, category_id):
    category = get_object_or_404(Category, pk = category_id )
    category.catchup(request.session, request.user)
    req = HttpResponseRedirect( '../../show/%s/' % category_id )
    req.sph_lastmodified = True
    return req


def latest_posts_of_user_context(request, group, user):
    allowed_categories = get_all_viewable_categories( group, request.user )
    post_list = Post.objects.filter( category__id__in = allowed_categories,
                                     author = user )
    post_list = post_list.order_by( '-postdate' )

    return { 'post_list': post_list,
             'post_user': user,
             }


def render_latest_posts_of_user(request, group, user):
    ctx = latest_posts_of_user_context(request,group,user)
    ctx['post_list'] = ctx['post_list'][0:10]
    str = template.loader.render_to_string( 'sphene/sphboard/_latest_posts_of_user.html',
                                            ctx,
                                            context_instance = RequestContext(request))

    return str

