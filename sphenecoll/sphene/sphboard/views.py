from datetime import timedelta

from django.core.paginator import Paginator
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext, ugettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from django.forms.models import modelformset_factory
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView

from sphene.community import PermissionDenied
from sphene.community.permissionutils import has_permission_flag
from sphene.community.middleware import get_current_sphdata
from sphene.community.sphutils import sph_reverse, get_user_displayname, format_date, get_sph_setting, add_rss_feed, \
    sph_render_to_response

from sphene.generic import advanced_object_list as objlist

from sphene.sphboard.forms import PollForm, PollChoiceForm, PostForm, \
    PostPollForm, PostAttachmentForm, \
    AnnotateForm, MoveAndAnnotateForm, MovePostForm
from sphene.sphboard.models import Category, Post, PostAnnotation, ThreadInformation, Poll, PollChoice, PollVoters, \
    POST_MARKUP_CHOICES, THREAD_TYPE_MOVED, THREAD_TYPE_DEFAULT, get_all_viewable_categories, ThreadLastVisit, \
    CategoryLastVisit, PostAttachment


class CategoryList(ListView):
    """
    displays either all root categories, or the contents of a category.
    the contents of a category could be other categories or forum threads.
    """

    paginate_by = 10
    context_object_name = 'thread_list'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prepared_context = {}
        self.request = None
        self.group = None

    def get(self, request, group=None, category_id=0, show_type=None, *args, **kwargs):
        category_id = category_id and int(category_id) or 0
        self.group = group
        self.request = request

        if group is None:
            raise Http404

        query_args = { 'group': group, 'parent__isnull': True }

        sphdata = get_current_sphdata()

        categories = []
        category = None

        if category_id:
            query_args['parent__isnull'] = False
            query_args['parent'] = category_id
            category = get_object_or_404(Category, pk=category_id)
            if not category.has_view_permission(request.user):
                raise PermissionDenied()
            category.touch(request.session, request.user)

            blog_feed_url = sph_reverse('sphboard-feeds', kwargs={'category_id': category.id})
            add_rss_feed(blog_feed_url, 'Latest Threads in %s RSS Feed' % category.name)

            if sphdata is not None:
                sphdata['subtitle'] = category.name
        elif sphdata is not None:
            sphdata['subtitle'] = ugettext('Forum Overview')

        if show_type != 'threads':
            categories = Category.sph_objects.filter(group=group)  # filter_for_group( args['group'] )
            if category:
                categories = categories.filter(parent=category)
            else:
                categories = categories.filter(parent__isnull=True)
            categories = [category for category in categories if category.has_view_permission(request.user)]

        self.prepared_context = {
            'rootCategories': categories,
            'category': category,
            'allowPostThread': category and category.allowPostThread(request.user),
            'category_id': category_id,
            'show_type': show_type,
        }

        try:
            self.prepared_context['search_posts_url'] = sph_reverse('sphsearchboard_posts')
        except:
            pass

        return super(CategoryList, self).get(request, *args, **kwargs)

    def get_template_names(self):
        category = self.prepared_context['category']

        # TODO is != 'threads' really correct here?!
        # if self.prepared_context['show_type'] == 'threads' \
        #         or category is None:
        if category is None:
            return 'sphene/sphboard/listCategories.html'

        category_type = category.get_category_type()
        return category_type.get_threadlist_template()

    def get_queryset(self):
        category = self.prepared_context['category']
        if category is None:
            if self.prepared_context['show_type'] != 'threads':
                # We are just showing the root categories, without any threads.
                return []

            # Show the latest threads from all categories.
            allowed_categories = get_all_viewable_categories(self.group, self.request.user)

            if self.group is not None:
                thread_args = {'category__group': self.group}
            else:
                thread_args = {'category__group__isnull': True}
            # thread_args[ 'thread__isnull'] = True
            thread_args['category__id__in'] = allowed_categories
            thread_args['root_post__is_hidden'] = 0
            self.prepared_context['isShowLatest'] = True
            thread_list = ThreadInformation.objects.filter(**thread_args)
        else:
            thread_list = category.get_thread_list()

        if self.prepared_context['show_type'] != 'threads':
            thread_list = thread_list.order_by('-sticky_value', '-thread_latest_postdate')
        else:
            thread_list = thread_list.order_by('-thread_latest_postdate')
        thread_list = thread_list.select_related('root_post', 'latest_post', 'root_post__category', 'root_post__author',
                                                 'latest_post__author')
        return thread_list


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return { **context, **self.prepared_context }


def listThreads(request, group, category_id):
    """
    THIS IS JUST FOR TESTING PURPOSES FOR NOW !!!
    """
    from sphene.sphboard.lists import ThreadList
    # TODO check permissions
    queryset = ThreadInformation.objects.filter(category__pk=category_id)
    queryset = queryset.select_related('root_post', 'latest_post', )
    threadlist = ThreadList(objlist.QuerySetProvider(queryset),
                            object_name=_('Threads'),
                            prefix='threadlist',
                            session=request.session,
                            requestvars=request.GET,
                            defaultsortby='latestpostdate',
                            defaultsortorder='desc',
                            defaultcolconfig=('newpost',
                                              ('subject',
                                               'author',),
                                              'views',
                                              'posts',
                                              ('latestpostdate',
                                               'latestpostauthor',),), )
    return sph_render_to_response('sphene/sphboard/new_list_threads.html',
                                  {'threadlist': threadlist, })


class ThreadListView(ListView):

    paginate_by = get_sph_setting('board_post_paging')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.thread: Post = None

    def get(self, request, group=None, thread_id=None, **kwargs):
        assert group

        self.thread = thread = get_object_or_404(Post.objects, pk=thread_id)
        if not thread.category.has_view_permission(request.user):
            raise PermissionDenied()
        thread.viewed(request.session, request.user)

        sphdata = get_current_sphdata()
        if sphdata is not None:
            sphdata['subtitle'] = thread.subject

        category_type = thread.category.get_category_type()
        self.template_name = category_type.get_show_thread_template()
        return super().get(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return {
            **context,
            'thread': self.thread,
            'allowPosting': self.thread.allowPosting(self.request.user),
            'postSubject': 'Re: ' + self.thread.subject,
            'category_type': self.thread.category.get_category_type(),
        }

    def get_queryset(self):
        return self.thread.get_all_posts().order_by('postdate')


def options(request, thread_id, group=None):
    thread = Post.objects.get(pk=thread_id)

    req = request.GET if request.method == 'GET' else request.POST

    if req['cmd'] == 'makeSticky':
        if not thread.allow_sticking(): raise PermissionDenied()
        thread.set_sticky(True)
    elif req['cmd'] == 'removeSticky':
        if not thread.allow_sticking(): raise PermissionDenied()
        thread.set_sticky(False)
    elif req['cmd'] == 'toggleClosed':
        if not thread.allow_locking(): raise PermissionDenied()
        thread.set_closed(not thread.is_closed())
    elif req['cmd'] == 'modifytags':
        if not request.user.is_superuser: raise PermissionDenied()
        from tagging.models import Tag
        Tag.objects.update_tags(thread.get_threadinformation(), [request.POST['tags'], ])

    thread.save()

    return HttpResponseRedirect(thread.get_absolute_url())


def reply(*args, **kwargs):
    return post(*args, **kwargs)


def enable_wysiwyg_editor():
    # we want the bbcode WYSIWYG editor only if 'bbcode' is the only
    # choice.
    return len(POST_MARKUP_CHOICES) == 1 and \
           POST_MARKUP_CHOICES[0][0] == 'bbcode' and \
           get_sph_setting('board_wysiwyg')


def post(request, group=None, category_id=None, post_id=None, thread_id=None):
    """
    View method to allow users to:
    - create new threads (post_id and thread_id is None)
    - reply to threads (post_id is None)
    - edit posts (post_id is the post which should be edited, thread_id is None)

    post_id and thread_id can either be passed in by URL (named parameters
    to this method) or by request.REQUEST parameters.
    """
    req = request.GET if request.method == 'GET' else request.POST
    if 'type' in req and req['type'] == 'preview':
        # If user just wants a preview, simply create a dummy post so it can be rendered.
        previewpost = Post(body=req['body'],
                           markup=req.get('markup', None))
        if request.user.is_authenticated:
            previewpost.author_id = request.user.pk
        return HttpResponse(str(previewpost.body_escaped()))

    # All available objects should be loaded from the _id variables.
    post_obj = None
    thread = None
    category = None
    context = {
        'bbcodewysiwyg': enable_wysiwyg_editor() or
                         (get_sph_setting('board_wysiwyg_testing') and req.get('wysiwyg', False))
    }

    if post_id is None and 'post_id' in req:
        # if no post_id is given take it from the request.
        post_id = req['post_id']

    if post_id is not None:
        # User wants to edit a post ..
        try:
            post_obj = Post.allobjects.get(pk=post_id)
        except Post.DoesNotExist:
            raise Http404

        if not post_obj.allowEditing():
            raise PermissionDenied()
        thread = post_obj.thread
        category = post_obj.category

    else:
        # User wants to create a new post (thread or reply)
        if 'thread' in req:
            thread_id = req['thread']

        if thread_id is not None:
            # User is posting (replying) to a thread.
            try:
                thread = Post.allobjects.get(pk=thread_id)
            except Post.DoesNotExist:
                raise Http404

            category = thread.category

            if not thread.allowPosting(request.user):
                raise PermissionDenied()
        else:
            # User is creating a new thread.
            category = get_object_or_404(Category, pk=category_id)
            if not category.allowPostThread(request.user):
                raise PermissionDenied()

    context['thread'] = thread
    context['category'] = category

    category_type = category.get_category_type()
    MyPostForm = PostForm
    if category_type is not None:
        MyPostForm = category_type.get_post_form_class(thread, post_obj)

    allow_attachments = get_sph_setting('board_allow_attachments')
    allowedattachments = 0
    if allow_attachments:
        allowedattachments = 1
        # bool is a subclass of int (hehe)
        if isinstance(allow_attachments, int) and type(allow_attachments) != bool:
            allowedattachments = allow_attachments

    PostAttachmentFormSet = modelformset_factory(PostAttachment,
                                                 form=PostAttachmentForm,
                                                 fields=('fileupload',),
                                                 can_delete=True,
                                                 max_num=allowedattachments)

    post_attachment_qs = PostAttachment.objects.none()
    if post_obj:
        post_attachment_qs = post_obj.attachments.all()

    if request.method == 'POST':
        postForm = MyPostForm(request.POST)
        postForm.init_for_category_type(category_type, post_obj)
        pollForm = PostPollForm(request.POST)

        create_post = True
        if allowedattachments and 'cmd_addfile' in request.POST:
            create_post = False

        post_attachment_formset = PostAttachmentFormSet(request.POST,
                                                        request.FILES,
                                                        queryset=post_attachment_qs,
                                                        prefix='attachment'
                                                        )

        if post_attachment_formset.is_valid():
            instances = post_attachment_formset.save(commit=False)
            for attachment in instances:
                if not post_obj:
                    # if there is no post yet.. we need to create a draft
                    post_obj = Post(category=category,
                                    author=request.user,
                                    thread=thread,
                                    is_hidden=1,
                                    )
                    post_obj.set_new(True)
                    post_obj.save()

                # Reference the post and save the attachment
                attachment.post = post_obj
                attachment.save()

        if create_post \
                and postForm.is_valid() \
                and ('createpoll' not in request.POST
                     or pollForm.is_valid()):
            data = postForm.cleaned_data

            if post_obj:
                newpost = post_obj
                newpost.subject = data['subject']
                newpost.body = data['body']
                # make post visible
                newpost.is_hidden = 0
                if not post_obj.is_new() and category_type.append_edit_message_to_post(post_obj):
                    newpost.body += "\n\n" + _(u'--- Last Edited by %(username)s at %(edit_date)s ---') % {
                        'username': get_user_displayname(request.user), 'edit_date': format_date(timezone.now())}
            else:
                user = request.user.is_authenticated and request.user or None
                newpost = Post(category=category,
                               subject=data['subject'],
                               body=data['body'],
                               author=user,
                               thread=thread,
                               )
            if 'markup' in data:
                newpost.markup = data['markup']

            elif len(POST_MARKUP_CHOICES) == 1:
                newpost.markup = POST_MARKUP_CHOICES[0][0]

            newpost.save(additional_data=data)

            # category_type.save_post( newpost, data )

            # Creating monitor
            if request.POST.get('addmonitor', False):
                newpost.toggle_monitor()

            if 'createpoll' in request.POST and request.POST['createpoll'] == '1':
                newpost.set_poll(True)
                newpost.save()

                # Creating poll...
                polldata = pollForm.cleaned_data
                newpoll = Poll(post=newpost,
                               question=polldata['question'],
                               choices_per_user=polldata['choicesPerUser'])
                newpoll.save()

                choices = polldata['answers'].splitlines()
                i = 0
                for choice in choices:
                    pollchoice = PollChoice(poll=newpoll,
                                            choice=choice,
                                            count=0,
                                            sortorder=i)
                    i += 1
                    pollchoice.save()
                if request.user.is_authenticated:
                    messages.success(request, message=ugettext(u'Vote created successfully.'))

            if request.user.is_authenticated:
                if post_obj:
                    messages.success(request, message=ugettext(u'Post edited successfully.'))
                else:
                    messages.success(request, message=ugettext(u'Post created successfully.'))
            if thread == None: thread = newpost
            return HttpResponseRedirect(newpost.get_absolute_url())

    else:
        postForm = MyPostForm()
        postForm.init_for_category_type(category_type, post_obj)
        pollForm = PostPollForm()

        post_attachment_formset = PostAttachmentFormSet(queryset=post_attachment_qs,
                                                        prefix='attachment')

    if post_obj:
        postForm.fields['subject'].initial = post_obj.subject
        postForm.fields['body'].initial = post_obj.body
        if 'markup' in postForm.fields:
            postForm.fields['markup'].initial = post_obj.markup
        context['post'] = post_obj
        context['thread'] = post_obj.thread or post_obj
    elif 'quote' in req:
        quotepost = get_object_or_404(Post, pk=req['quote'])
        postForm.fields['subject'].initial = 'Re: %s' % thread.subject
        if quotepost.author is None:
            username = 'anonymous'
        else:
            username = quotepost.author.username
        postForm.fields['body'].initial = '[quote=%s;%s]\n%s\n[/quote]\n' % (username, quotepost.id, quotepost.body)
    elif thread:
        postForm.fields['subject'].initial = 'Re: %s' % thread.subject
    context['form'] = postForm

    # Only allow polls if this is a new _thread_ (not a reply)
    if (not thread and not post_obj) or (post_obj and post_obj.is_new() and post_obj.thread is None):
        context['pollform'] = pollForm
    context['post_attachment_formset'] = post_attachment_formset
    if 'createpoll' in req:
        context['createpoll'] = req['createpoll']

    res = render(request,
                 "sphene/sphboard/post.html",
                 context)
    # Maybe the user is in the 'edit' form, which should not be cached.
    res.sph_lastmodified = True
    return res


def edit_poll(request, group, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if not poll.allow_editing():
        raise PermissionDenied()

    postdata = None
    if request.method == 'POST':
        postdata = request.POST

    form = PollForm(postdata, instance=poll)
    choiceforms = [PollChoiceForm(postdata,
                                  prefix='choice_%d' % choice.id,
                                  instance=choice,
                                  ) for choice in poll.pollchoice_set.all()]

    if request.method == 'POST' and form.is_valid() \
            and not [True for choiceform in choiceforms if not choiceform.is_valid()]:
        form.save()
        for choiceform in choiceforms:
            choiceform.save()

        return HttpResponseRedirect(sph_reverse('sphene.sphboard.views.showThread',
                                                kwargs={'thread_id': poll.post.get_thread().id}))

    return sph_render_to_response('sphene/sphboard/edit_poll.html',
                                  {'form': form,
                                   'choiceforms': choiceforms,
                                   })


def annotate(request, group, post_id):
    post = Post.objects.get(pk=post_id)
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
                annotation = PostAnnotation(post=post, )
            annotation.body = data['body']
            annotation.hide_post = data['hide_post']
            annotation.markup = data['markup']
            annotation.save()
            messages.success(request, message=ugettext(u'Annotated a users post.'))
            return HttpResponseRedirect(post.get_absolute_url())

    else:
        form = AnnotateForm()

    if annotation is not None:
        form.fields['body'].initial = annotation.body
        form.fields['hide_post'].initial = annotation.hide_post
        if 'markup' in form.fields:
            form.fields['markup'].initial = annotation.markup

    return render(
        request,
        "sphene/sphboard/annotate.html",
        {'thread': thread,
         'post': post,
         'form': form}
    )


def hide(request, group, post_id):
    """ Delete post by setting is_hidden=True
        (annotate method above allows to hide content of the post but leaves it in thread)
    """
    post_obj = get_object_or_404(Post, pk=post_id)
    thread = post_obj.get_thread()
    if not post_obj.allow_hiding():
        raise PermissionDenied()

    if request.method == 'POST' and 'hide-post' in request.POST.keys():
        post_obj.hide()
        messages.success(request, message=ugettext(u'Post deleted'))
        if post_obj == thread:
            return HttpResponseRedirect(post_obj.category.get_absolute_url())
        return HttpResponseRedirect(thread.get_absolute_url())

    return render(
        request,
        "sphene/sphboard/hide.html",
        {'thread': thread,
         'post': post_obj}
    )


def move_post_1(request, group, post_id):
    """
        Display list of categories where the post can be moved to.
    """
    post_obj = Post.objects.get(pk=post_id)
    if not post_obj.allow_moving_post():
        raise PermissionDenied()
    categories = get_all_viewable_categories(group, request.user)
    categories = Category.objects.filter(pk__in=categories)
    return render(
        request,
        "sphene/sphboard/move_post_1.html",
        {'categories': categories,
         'post': post_obj}
    )


def move_post_2(request, group, post_id, category_id):
    """
        Display threads in category (category_id) where the post
        can be moved to
    """
    post_obj = Post.objects.get(pk=post_id)
    if not post_obj.allow_moving_post():
        raise PermissionDenied()

    thread = post_obj.get_thread()
    category = Category.objects.get(pk=category_id)
    thread_list = category.get_thread_list().exclude(root_post=thread.pk).order_by('-thread_latest_postdate')

    paginator = Paginator(thread_list, get_sph_setting('board_post_paging'), allow_empty_first_page=True)

    page = request.GET.get('page')
    page_obj = paginator.get_page(page)

    # res = object_list(request=request,
    #                   queryset=thread_list,
    #                   allow_empty=True,
    #                   template_name="sphene/sphboard/move_post_2.html",
    #                   extra_context={'post': post_obj,
    #                                  'category': category},
    #                   template_object_name='thread',
    #                   paginate_by=get_sph_setting('board_post_paging')
    #                   )
    return render(request, 'sphene/sphboard/move_post_2.html', {
        'post': post_obj,
        'category': category,
        'thread_list': page_obj,
    })


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
            move_all_posts = data['move_all_posts']

            # information about thread from which moved post is taken
            threadinfo = post.get_threadinformation()
            next_posts = None
            if move_all_posts:
                next_posts = Post.objects.filter(thread=post.get_thread(), postdate__gt=post.postdate).order_by(
                    'postdate')

            # if moved post is root post of the thread then detach rest of
            # the posts
            if is_root_post:
                posts = Post.objects.filter(thread=post).order_by('postdate')
                # if there are subsequent posts
                if posts.count() > 0 and not move_all_posts:
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
                    threadinfo = None
                else:
                    # if post is moved to new category
                    # just update threadinfo
                    threadinfo.category = target_category
                    # threadinfo.update_cache()
                    # threadinfo.save()

            post.category = target_category
            post.thread = target_thread  # this might be None if post was moved into category
            if target_thread:
                # update postdate if necessary to achieve proper ordering (post is always added at the end)
                if target_thread.get_latest_post().postdate > post.postdate:
                    post.postdate = timezone.now()

            if body:
                post.set_annotated(True)
                if annotation is None:
                    annotation = PostAnnotation(post=post)
                annotation.body = body
                annotation.hide_post = False
                annotation.markup = data['markup']
                annotation.save()
            post.save()

            if not next_posts is None:
                # if posts were moved to new thread update postdate to place them at the end
                if target_thread:
                    cnt = 1
                    for p in next_posts:
                        p.thread = post.get_thread()
                        if post.postdate > p.postdate:
                            p.postdate = timezone.now() + timedelta(microseconds=cnt)
                        p.save()
                        cnt += 1
                elif not is_root_post:  # posts moved to category
                    next_posts.update(thread=post.get_thread())
                    # clear caches
                    for p in next_posts:
                        cache.delete(p._cache_key_absolute_url())

            # update information about thread from which post was moved
            if threadinfo:
                threadinfo.update_cache()
                threadinfo.save()

            if target_thread:
                messages.success(request, message=ugettext(u'Post has been appended to thread.'))
            else:
                messages.success(request, message=ugettext(u'Post has been moved into category.'))

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
        form.fields['body'].initial = _(u'This post was moved from the thread %(thread_name)s') % {
            'thread_name': thread_name}
    else:
        form.fields['body'].initial = _(u'This post was moved from the category %(category_name)s') % {
            'category_name': category_name}

    return render(
        request,
        "sphene/sphboard/move_post_3.html",
        {'thread': thread,
         'form': form,
         'post': post,
         'target_thread': target_thread,
         'is_root_post': is_root_post,
         'category': target_category
         })


def move(request, group, thread_id):
    thread = get_object_or_404(Post, pk=thread_id)
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
                newthreadinfo = ThreadInformation.objects.get(root_post=thread,
                                                              category=newcategory,
                                                              thread_type=THREAD_TYPE_MOVED)
            except ThreadInformation.DoesNotExist:
                newthreadinfo = ThreadInformation(root_post=thread,
                                                  category=newcategory, )

            newthreadinfo.thread_type = THREAD_TYPE_DEFAULT
            newthreadinfo.update_cache()
            newthreadinfo.save()

            thread.set_annotated(True)

            if annotation is None:
                annotation = PostAnnotation(post=thread, )
            annotation.body = data['body']
            annotation.hide_post = False
            annotation.markup = data['markup']
            annotation.save()

            thread.category = newcategory
            thread.save()

            # update category of thread's posts
            thread.replies().update(category=newcategory)

            messages.success(request, message=ugettext(u'Moved thread into new category.'))

            return HttpResponseRedirect(thread.get_absolute_url())

    else:
        form = MoveAndAnnotateForm()

    if POST_MARKUP_CHOICES[0][0] == 'bbcode':
        category_name = '[url=%s]%s[/url].' % (thread.category.get_absolute_url(), thread.category.name)
    else:
        category_name = thread.category.name
    form.fields['body'].initial = _(u'This thread was moved from the category %(category_name)s') % {
        'category_name': category_name}

    return render(
        request,
        "sphene/sphboard/move.html",
        {'thread': thread,
         'form': form}
    )


def delete_moved_info(request, group, pk):
    """ Delete information about moved thread
    """
    th = get_object_or_404(ThreadInformation, pk=pk)
    if not th.allow_deleting_moved(request.user):
        raise PermissionDenied()

    if request.method == 'POST' and 'delete-th' in request.POST.keys():
        back_url = th.category.get_absolute_url()
        th.delete()
        messages.success(request, message=ugettext(u'Information about moved thread has been deleted'))
        return HttpResponseRedirect(back_url)

    return render(
        request,
        "sphene/sphboard/delete_moved_info.html",
        {'th': th}
    )


def vote(request, group=None, thread_id=None):
    req = request.GET if request.method == 'GET' else request.POST

    thread = get_object_or_404(Post, pk=thread_id)

    poll = thread.poll()
    if poll.has_voted(request.user):
        request.attributes['voteerror'] = _(u'You have already voted.')
        return showThread(request, thread_id, group)

    if 'pollchoice' not in req or len(req['pollchoice']) < 1:
        request.attributes['voteerror'] = _(u'Please select at least one answer.')
        return showThread(request, thread_id, group)

    pollchoices = req.getlist('pollchoice')

    if poll.choices_per_user < len(pollchoices):
        request.attributes['voteerror'] = _(u'Please only select %(choices)d answers.') % {
            'choices': poll.choices_per_user}
        return showThread(request, thread_id, group)

    if len(pollchoices) > 1 and '0' in pollchoices:
        request.attributes['voteerror'] = _(
            u'You cannot abstain from voting and at the same time select a valid answer.')
        return showThread(request, thread_id, group)

    for pollchoice in pollchoices:
        if pollchoice == '0':
            choice = None
        else:
            try:
                choice = poll.pollchoice_set.get(pk=pollchoice)
            except PollChoice.DoesNotExist:
                request.attributes['voteerror'] = _(u"You've selected an invalid choice.")
                return showThread(request, thread_id, group)
            choice.count = choice.count + 1
            choice.save()
        voter = PollVoters(poll=poll,
                           choice=choice,
                           user=request.user, )
        voter.save()
        messages.success(request, message=choice and ugettext(u"Voted for '%(choice)s'.") % {
            'choice': choice.choice} or ugettext(u'You selected to abstain from voting'))

    return HttpResponseRedirect(thread.get_absolute_url())


def toggle_monitor(request, group, monitortype, object_id, monitor_user_id=None):
    if not request.user.is_authenticated:
        raise PermissionDenied()
    obj = None
    if monitortype == 'group':
        obj = group
        object_id = 0
    elif monitortype == 'category':
        obj = Category.objects.get(pk=object_id)
    elif monitortype == 'thread':
        obj = Post.objects.get(pk=object_id)

    new_monitor = None
    if monitor_user_id:
        monitor_user = User.objects.get(pk=monitor_user_id)
        new_monitor = obj.toggle_monitor(user=monitor_user)
    else:
        new_monitor = obj.toggle_monitor()

    if new_monitor:
        messages.success(request, message=ugettext(u'Successfully created email notification monitor.'))
    else:
        messages.success(request, message=ugettext(u'Removed email notification monitor.'))

    if 'next' in request.GET:
        return HttpResponseRedirect(request.GET['next'])
    if monitortype == 'group':
        return HttpResponseRedirect(sph_reverse('sphboard-index'))
    return HttpResponseRedirect(obj.get_absolute_url())


@login_required
def catchup(request, group, category_id):
    if category_id == '0':
        ThreadLastVisit.objects.filter(user=request.user).delete()
        CategoryLastVisit.objects.filter(user=request.user).update(lastvisit=timezone.now(), oldlastvisit=None)
        req = HttpResponseRedirect(sph_reverse('sphboard-index'))
    else:
        category = get_object_or_404(Category, pk=category_id)
        category.catchup(request.session, request.user)
        req = HttpResponseRedirect(
            sph_reverse('sphene.sphboard.views.showCategory', kwargs={'category_id': category_id}))

    req.sph_lastmodified = True
    return req


def latest_posts_of_user_context(request, group, user):
    allowed_categories = get_all_viewable_categories(group, request.user)
    post_list = Post.objects.filter(category__id__in=allowed_categories,
                                    author=user)
    post_list = post_list.order_by('-postdate')

    return {'post_list': post_list,
            'post_user': user,
            }


def render_latest_posts_of_user(request, group, user):
    ctx = latest_posts_of_user_context(request, group, user)
    ctx['post_list'] = ctx['post_list'][0:10]
    return render(
        request,
        'sphene/sphboard/_latest_posts_of_user.html',
        ctx)


def admin_user_posts(request, group, user_id):
    if not has_permission_flag(request.user, 'community_manage_users'):
        raise PermissionDenied()

    user = get_object_or_404(User, pk=user_id)

    orderby = request.GET.get('orderby', '-postdate')
    post_list = Post.objects.filter(author=user).order_by(orderby)

    template_name = 'sphene/sphboard/admin_user_posts.html'
    context = {'author': user,
               'orderby': orderby}

    res = object_list(request=request,
                      queryset=post_list,
                      template_name=template_name,
                      template_object_name='post',
                      extra_context=context,
                      allow_empty=True,
                      paginate_by=10,
                      )
    return res


def admin_post_delete(request, group, user_id, post_id):
    post_obj = get_object_or_404(Post, author=user_id, pk=post_id)
    if not post_obj.allow_hiding():
        raise PermissionDenied()
    post_obj.hide()
    messages.success(request, message=ugettext(u'Post deleted'))
    return HttpResponseRedirect(sph_reverse('sphboard_admin_user_posts', kwargs={'user_id': user_id}))


def admin_posts_delete(request, group, user_id):
    posts = Post.objects.filter(author=user_id)
    if posts:
        if not posts[0].allow_hiding():
            raise PermissionDenied()
        for post_obj in posts:
            post_obj.hide()
        messages.success(request, message=ugettext(u'All posts deleted'))
    else:
        messages.success(request, message=ugettext(u'No posts to delete'))
    return HttpResponseRedirect(sph_reverse('sphboard_admin_user_posts', kwargs={'user_id': user_id}))
