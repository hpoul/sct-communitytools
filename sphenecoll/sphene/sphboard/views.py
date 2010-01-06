from datetime import datetime

from django import template
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.template.context import RequestContext
from django.utils.translation import ugettext, ugettext_lazy as _

from sphene.community import PermissionDenied
from sphene.community.middleware import get_current_sphdata
from sphene.community.sphutils import sph_reverse, get_user_displayname, format_date, get_sph_setting, add_rss_feed, sph_render_to_response

from sphene.generic import advanced_object_list as objlist

from sphene.sphboard.forms import PollForm, PollChoiceForm, PostForm, \
                                  PostPollForm, PostAttachmentForm, \
                                  AnnotateForm, MoveAndAnnotateForm, MovePostForm
from sphene.sphboard.models import Category, Post, PostAnnotation, ThreadInformation, Poll, PollChoice, PollVoters, POST_MARKUP_CHOICES, THREAD_TYPE_MOVED, THREAD_TYPE_DEFAULT, get_all_viewable_categories, ThreadLastVisit, CategoryLastVisit


def showCategory(request, group, category_id = None, showType = None, slug = None):
    """
    displays either all root categories, or the contents of a category.
    the contents of a category could be other categories or forum threads.

    TODO: clean this mess up - sorry for everyone who trys to understand
    this function - this is is probably the oldest and ugliest in 
    the whole SCT source.

    We no longer support having no group !!
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
        blog_feed_url = sph_reverse('sphboard-feeds', kwargs = { 'url': 'latest/%s' % categoryObject.id })
        add_rss_feed( blog_feed_url, 'Latest Threads in %s RSS Feed' % categoryObject.name )

        if sphdata != None: sphdata['subtitle'] = categoryObject.name
    elif sphdata is not None:
        sphdata['subtitle'] = ugettext('Forum Overview')

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
                            object_name = _( 'Threads' ),
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


def showThread(request, thread_id, group = None, slug = None):
    thread = get_object_or_404(Post.objects, pk = thread_id )
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

    if request.REQUEST['cmd'] == 'makeSticky':
        if not thread.allow_sticking(): raise PermissionDenied()
        thread.set_sticky(True)
    elif request.REQUEST['cmd'] == 'removeSticky':
        if not thread.allow_sticking(): raise PermissionDenied()
        thread.set_sticky(False)
    elif request.REQUEST['cmd'] == 'toggleClosed':
        if not thread.allow_locking(): raise PermissionDenied()
        thread.set_closed(not thread.is_closed())
    elif request.REQUEST['cmd'] == 'modifytags':
        if not request.user.is_superuser: raise PermissionDenied()
        from tagging.models import Tag
        Tag.objects.update_tags( thread.get_threadinformation(), [request.POST['tags'], ] )

    thread.save()
    
    return HttpResponseRedirect( thread.get_absolute_url() )

def reply(*args, **kwargs):
    return post(*args, **kwargs)


def enable_wysiwyg_editor():
    # we want the bbcode WYSIWYG editor only if 'bbcode' is the only
    # choice.
    return len( POST_MARKUP_CHOICES ) == 1 and \
        POST_MARKUP_CHOICES[0][0] == 'bbcode' and \
        get_sph_setting('board_wysiwyg')

def post(request, group = None, category_id = None, post_id = None, thread_id = None):
    """
    View method to allow users to:
    - create new threads (post_id and thread_id is None)
    - reply to threads (post_id is None)
    - edit posts (post_id is the post which should be edited, thread_id is None)

    post_id and thread_id can either be passed in by URL (named parameters 
    to this method) or by request.REQUEST parameters.
    """
    if 'type' in request.REQUEST and request.REQUEST['type'] == 'preview':
        # If user just wants a preview, simply create a dummy post so it can be rendered.
        previewpost = Post( body = request.REQUEST['body'],
                            markup = request.REQUEST.get('markup', None), )
        return HttpResponse( unicode(previewpost.body_escaped()) )


    # All available objects should be loaded from the _id variables.
    post = None
    thread = None
    category = None
    context = {
        'bbcodewysiwyg': enable_wysiwyg_editor() \
            or (get_sph_setting('board_wysiwyg_testing') \
                    and request.REQUEST.get('wysiwyg', False)) }
    
    if post_id is None and 'post_id' in request.REQUEST:
        # if no post_id is given take it from the request.
        post_id = request.REQUEST['post_id']

    if post_id is not None:
        # User wants to edit a post ..
        try:
            post = Post.allobjects.get( pk = post_id )
        except Post.DoesNotExist:
            raise Http404

        if not post.allowEditing():
            raise PermissionDenied()
        thread = post.thread
        category = post.category
    
    else:
        # User wants to create a new post (thread or reply)
        if 'thread' in request.REQUEST:
            thread_id = request.REQUEST['thread']

        if thread_id is not None:
            # User is posting (replying) to a thread.
            try:
                thread = Post.allobjects.get( pk = thread_id )
            except Post.DoesNotExist:
                raise Http404

            category = thread.category
        
            if not thread.allowPosting( request.user ):
                raise PermissionDenied()
        else:
            # User is creating a new thread.
            category = get_object_or_404(Category, pk = category_id)
            if not category.allowPostThread( request.user ):
                raise PermissionDenied()

    context['thread'] = thread
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
                
            newpost.save(additional_data = data)

            #category_type.save_post( newpost, data )


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

def annotate(request, group, post_id):
    post = Post.objects.get( pk = post_id )
    thread = post.get_thread()
    if not thread.allow_annotating():
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

def hide(request, group, post_id):
    post = Post.objects.get( pk = post_id )
    thread = post.get_thread()
    if not post.allow_hiding():
        raise PermissionDenied()

    if request.method == 'POST' and 'hide-post' in request.POST.keys():
        if post.thread is None: # this is root post of thread
            Post.objects.filter(thread = post).update(is_hidden = 1)
        post.is_hidden = 1
        post.save()
        request.user.message_set.create( message = ugettext(u'Post deleted') )
        if post == thread:
            return HttpResponseRedirect( post.category.get_absolute_url() )
        return HttpResponseRedirect( thread.get_absolute_url() )

    return render_to_response( "sphene/sphboard/hide.html",
                               { 'thread': thread,
                                 'post': post
                                 },
                               context_instance = RequestContext(request) )

def move_post_1(request, group, post_id):
    """
        Display list of categories where the post can be moved to.
    """
    post = Post.objects.get(pk=post_id)
    if not post.allow_moving_post():
        raise PermissionDenied()
    categories = get_all_viewable_categories(group, request.user)
    categories = Category.objects.filter(pk__in=categories)
    return render_to_response("sphene/sphboard/move_post_1.html",
                              {'categories': categories,
                               'post': post},
                              context_instance = RequestContext(request))

def move_post_2(request, group, post_id, category_id):
    """
        Display threads in category (category_id) where the post
        can be moved to
    """
    post = Post.objects.get(pk=post_id)
    if not post.allow_moving_post():
        raise PermissionDenied()

    thread = post.get_thread()
    category = Category.objects.get(pk=category_id)
    thread_list = category.get_thread_list().exclude(root_post=thread.pk).order_by('-thread_latest_postdate')

    res =  object_list(request = request,
                       queryset = thread_list,
                       allow_empty = True,
                       template_name = "sphene/sphboard/move_post_2.html",
                       extra_context = {'post': post,
                                        'category':category},
                       template_object_name = 'thread',
                       paginate_by = get_sph_setting('board_post_paging')
                      )
    return res

def move_post_3(request, group, post_id, category_id, thread_id=None):
    """
        @post_id - moved post id
        @category_id - target category id
        @thread_id - target thread id (if exists)

        Post might be moved direclty into category - in this case post becomes
        thread or post might be inserted into another thread.
    """
    post = Post.objects.get(pk=post_id)

    # determine if moved post is root post of thread
    thread = post.get_thread()
    is_root_post = thread.pk == post.pk

    target_thread = None
    if thread_id:
        target_thread = get_object_or_404(Post, pk=thread_id)
    
    if not post.allow_moving_post() or thread == target_thread:
        raise PermissionDenied()

    target_category = Category.objects.get(pk=category_id)

    # moved post will be annotated
    annotation = None
    if post.is_annotated():
        try:
            annotation = post.annotation.get()
        except PostAnnotation.DoesNotExist:
            pass
    if request.method == 'POST':
        form = MovePostForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            body = data['body']

            # information about thread from which moved post is taken
            threadinfo = post.get_threadinformation()

            # if moved post is root post of the thread then detach rest of
            # the posts
            if is_root_post:
                posts = Post.objects.filter(thread=post).order_by('postdate')
                # if there are subsequent posts
                if posts.count()>0:
                    # prepare new root_post
                    new_root = posts[0]
                    new_root.thread = None
                    posts.exclude(pk=new_root.pk).update(thread=new_root)
                    new_root.save()
                    # new threadinfo is automatically created by signal while saving Post

                if target_thread:
                    # if root post is moved into another thread then
                    # remove threadinfo
                    threadinfo.delete()
                else:
                    # if post is moved to new category
                    # just update threadinfo
                    threadinfo.category=target_category
                    #threadinfo.update_cache()
                    #threadinfo.save()

            post.category = target_category
            post.thread = target_thread  # this might be None if post was moved into category
            if target_thread:
                # update postdate if necessary to achieve proper ordering (post is always added at the end)
                if target_thread.get_latest_post().postdate>post.postdate:
                    post.postdate = datetime.now()

            if body:
                post.set_annotated(True)
                if annotation is None:
                    annotation = PostAnnotation(post=post)
                annotation.body = body
                annotation.hide_post = False
                annotation.markup = data['markup']
                annotation.save()
            post.save()

            # update information about thread from which post was moved
            threadinfo.update_cache()
            threadinfo.save()

            if target_thread:
                request.user.message_set.create(message=ugettext(u'Post has been appended to thread.'))
            else:
                request.user.message_set.create(message=ugettext(u'Post has been moved into category.'))

            return HttpResponseRedirect(post.get_absolute_url())
    else:
        form = MovePostForm()

    if POST_MARKUP_CHOICES[0][0] == 'bbcode':
        category_name = '[url=%s]%s[/url].' % (post.category.get_absolute_url(),
                                               post.category.name)
        thread_name = '[url=%s]%s[/url].' % (thread.get_absolute_url(),
                                             thread.subject)
    else:
        category_name = post.category.name
        thread_name = thread.subject

    if not is_root_post:
        form.fields['body'].initial = _(u'This post was moved from the thread %(thread_name)s') % {'thread_name':thread_name}
    else:
        form.fields['body'].initial = _(u'This post was moved from the category %(category_name)s') % {'category_name':category_name}

    return render_to_response( "sphene/sphboard/move_post_3.html",
                               { 'thread': thread,
                                 'form': form,
                                 'post':post,
                                 'target_thread':target_thread,
                                 'is_root_post':is_root_post,
                                 'category':target_category
                                 },
                               context_instance = RequestContext(request))

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
            info_link = data['info_link']

            threadinfo = thread.get_threadinformation()

            if info_link:
                threadinfo.thread_type = THREAD_TYPE_MOVED
                threadinfo.save()
            else:
                threadinfo.delete()

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
    

    return HttpResponseRedirect( thread.get_absolute_url() )

def toggle_monitor(request, group, monitortype, object_id):
    if not request.user.is_authenticated():
        raise PermissionDenied()
    obj = None
    if monitortype == 'group':
        obj = group
        object_id = 0
    elif monitortype == 'category':
        obj = Category.objects.get( pk = object_id )
    elif monitortype == 'thread':
        obj = Post.objects.get( pk = object_id )

    if obj.toggle_monitor():
        request.user.message_set.create( message = ugettext(u'Successfully created email notification monitor.') )
    else:
        request.user.message_set.create( message = ugettext(u'Removed email notification monitor.') )

    if 'next' in request.GET:
        return HttpResponseRedirect( request.GET['next'] )
    if monitortype == 'group':
        return HttpResponseRedirect( sph_reverse( 'sphboard-index' ) )
    return HttpResponseRedirect( obj.get_absolute_url() )

def catchup(request, group, category_id):
    if category_id == '0':
        ThreadLastVisit.objects.filter(user = request.user).delete() 
        CategoryLastVisit.objects.filter(user = request.user).update(lastvisit = datetime.today(), oldlastvisit = None)
        req = HttpResponseRedirect(sph_reverse('sphboard-index'))
    else:
        category = get_object_or_404(Category, pk = category_id )
        category.catchup(request.session, request.user)
        req = HttpResponseRedirect( sph_reverse('sphene.sphboard.views.showCategory' , kwargs = {'category_id': category_id } ) )

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

