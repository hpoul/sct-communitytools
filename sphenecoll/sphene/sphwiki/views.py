from django import forms
from django.forms import widgets, ModelForm
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext, ugettext_lazy

from datetime import datetime
from difflib import HtmlDiff

from django.views.generic import ListView

from sphene.sphwiki.models import WikiSnip, WikiSnipChange, WikiAttachment
from sphene.community import PermissionDenied, sphutils
from sphene.community.middleware import get_current_sphdata, get_current_user
from sphene.community.models import Tag, tag_set_labels, tag_get_labels, tag_get_models_by_tag, \
    Group
from sphene.community.fields import TagField


# Create your views here.


def showSnip(request, group, snipName):
    snip_rendered_body = None
    status = None
    try:
        snip = WikiSnip.objects.get(group=group,
                                    name__exact=snipName)
    except WikiSnip.DoesNotExist:
        snip = WikiSnip(name=snipName, group=group)
        status = 404

    if not snip.has_view_permission():
        raise PermissionDenied()

    res = None
    if 'type' in request.GET:
        if request.GET['type'] == 'src':
            res = HttpResponse(snip.body, mimetype='text/plain', )
        if request.GET['type'] == 'full':
            res = HttpResponse(snip.render(), mimetype='text/html', )

    if not res:
        sphdata = get_current_sphdata()
        snip_rendered_body = False
        redirects = ()
        while not snip_rendered_body or 'sphwiki_redirect_to_snip' in sphdata:
            if snip_rendered_body:
                if snip in redirects:
                    if request.user.is_authenticated:
                        messages.success(request, message=ugettext("Detected redirect loop."))
                    break
                redirects += (snip,)
                snip = sphdata['sphwiki_redirect_to_snip']
                del sphdata['sphwiki_redirect_to_snip']
            snip_rendered_body = snip.render()

        if sphdata is not None: sphdata['subtitle'] = snip.title or snip.name

        res = render(request,
                     'sphene/sphwiki/showSnip.html',
                     {'snip': snip,
                      'snipName': snipName,
                      'snip_rendered_body': snip_rendered_body,
                      'redirects': redirects,
                      'commentstemplate': 'sphene.sphcomments' in settings.INSTALLED_APPS and 'sphene/sphwiki/wikicomments.html' or 'sphene/sphwiki/wikicomments_unavailable.html',
                      })

    if status is not None:
        res.status_code = status
    res.sph_lastmodified = snip.changed
    return res


def generatePDF(request, group, snipName):
    if not hasattr(settings, 'SPH_SETTINGS'):
        return HttpResponse(ugettext('Not configured.'))

    snip = get_object_or_404(WikiSnip,
                             group=group,
                             name=snipName)
    if not snip.has_view_permission():
        raise PermissionDenied()

    try:
        contents = open(snip.pdf_get(), 'rb').read()
    except Exception as e:
        import logging
        logging.exception('Error while generating PDF file.')
        # return HttpResponse(ugettext('Error while generating PDF file. %(error)s') % \
        #                        { 'error': str(e) })
        raise e

    response = HttpResponse(contents, mimetype='application/pdf')

    return response


class HistoryListView(ListView):
    group: Group
    snip: WikiSnip

    template_name = 'sphene/sphwiki/history.html'
    allow_empty = True
    paginate_by = 50

    # noinspection PyMethodOverriding
    def get(self, request, group, snipName, *args, **kwargs):
        self.snip = get_object_or_404(WikiSnip, group=group, name=snipName)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.snip.wikisnipchange_set.order_by('-edited')


class RecentChangesListView(ListView):
    template_name = 'sphene/sphwiki/recentChanges.html'
    allow_empty = True
    group: Group
    paginate_by = 50

    def get(self, request, group=None, *args, **kwargs):
        self.group = group
        res = super().get(request, *args, **kwargs)
        res.sph_lastmodified = True
        return res

    def get_queryset(self):
        return WikiSnipChange.objects.filter(snip__group=self.group).order_by('-edited')


def diff(request, group, snipName, changeId=None):
    snip = get_object_or_404(WikiSnip,
                             group=group,
                             name=snipName)
    if not snip.has_view_permission():
        raise PermissionDenied()
    change_end = get_object_or_404(WikiSnipChange,
                                   snip=snip,
                                   pk=changeId, )
    args = {'snip': snip,
            'snipName': snipName, }
    try:
        change_start = snip.wikisnipchange_set.filter(edited__lt=change_end.edited, ).order_by('-edited')[0]
        args['prev_change'] = change_start
    except IndexError:
        change_start = None
        diff_table = ugettext("This is the first change.")

    try:
        next_change = snip.wikisnipchange_set.filter(edited__gt=change_end.edited, ).order_by('edited')[0]
        args['next_change'] = next_change
    except IndexError:
        pass

    if change_start:
        html_diff = HtmlDiff(wrapcolumn=50, )
        from sphene.community.templatetags.sph_extras import sph_date, sph_user_displayname
        desc = ugettext('%(date)s by %(editor)s')
        if snip.has_edit_permission():
            desc += ' / <a href="%(editversionlink)s">' + ugettext('Edit this version') + '</a>'
        fromdesc = desc % {
            'date': sph_date(change_start.edited),
            'editor': sph_user_displayname(change_start.editor),
            'editversionlink': change_start.get_absolute_editurl()},
        todesc = desc % {
            'date': sph_date(change_end.edited),
            'editor': sph_user_displayname(change_end.editor),
            'editversionlink': change_end.get_absolute_editurl()},

        diff_table = html_diff.make_table(change_start.body.splitlines(True),
                                          change_end.body.splitlines(True),
                                          fromdesc=fromdesc,
                                          todesc=todesc,
                                          context=True, )

    args['diffTable'] = mark_safe(diff_table)
    args['fromchange'] = change_start
    args['tochange'] = change_end
    return render(request,
                  'sphene/sphwiki/diff.html',
                  args)


def attachment(request, group, snipName):
    snip = WikiSnip.objects.get(name__exact=snipName, group=group)
    if not snip.has_view_permission():
        raise PermissionDenied()
    res = WikiAttachment.objects.filter(snip=snip)
    return object_list(request=request,
                       queryset=WikiAttachment.objects.filter(snip=snip),
                       template_name='sphene/sphwiki/listAttachments.html',
                       extra_context={'snipName': snipName,
                                      'snip': snip,
                                      },
                       allow_empty=True)


def attachmentCreate(request, group, snipName, attachmentId=None):
    """ Sick workaround for reverse lookup. """
    return attachmentEdit(request, group, snipName, attachmentId)


def attachmentEdit(request, group, snipName, attachmentId=None):
    """Importing ModelForm"""
    from django.forms import ModelForm

    """ Class necessary for the Modelform """

    class AttachmentFormNew(ModelForm):
        class Meta:
            model = WikiAttachment

    attachment = None
    if attachmentId is None:
        AttachmentForm = AttachmentFormNew()
    else:
        attachment = WikiAttachment.objects.get(id=attachmentId)
        AttachmentForm = AttachmentFormNew(instance=attachment)

    if attachment:
        if not attachment.snip.has_edit_permission():
            raise PermissionDenied()
    if 'delete' in request.GET and request.GET['delete'] == '1':
        attachment.delete()
        messages.success(request, message=ugettext("Successfully deleted attachment."))
        return HttpResponseRedirect(attachment.snip.get_absolute_attachmenturl())

    AttachmentForm.base_fields['fileupload'].widget = widgets.FileInput()

    if request.method == 'POST':
        form = AttachmentFormNew(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            snip = WikiSnip.objects.get(name__exact=snipName, group=group)
            attachment.snip = snip
            attachment.uploader = request.user
            attachment.save()
            return HttpResponseRedirect(snip.get_absolute_attachmenturl())
    else:
        form = AttachmentFormNew(instance=attachment)

    return render(request,
                  'sphene/sphwiki/editAttachment.html',
                  {'form': form,
                   'snipName': snipName,
                   })


class CaptchaEditBaseForm(forms.BaseForm):
    """ BaseForm which displays a captcha, if required. """

    def __init__(self, *args, **kwargs):
        super(CaptchaEditBaseForm, self).__init__(*args, **kwargs)

        if sphutils.has_captcha_support() and not get_current_user().is_authenticated:
            self.fields['captcha'] = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
                                                           help_text=ugettext(
                                                               'Please enter the result of the above calculation.'),
                                                           )
        self.fields['tags'] = TagField(model=WikiSnip, required=False)


class WikiSnipForm(ModelForm):
    tags = TagField(model=WikiSnip, required=False)
    captcha = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
                                    help_text=ugettext_lazy(u'Please enter the result of the above calculation.'),
                                    )

    def __init__(self, *args, **kwargs):
        super(WikiSnipForm, self).__init__(*args, **kwargs)
        self.fields['body'].widget.attrs['cols'] = 80
        self.fields['body'].widget.attrs['rows'] = 30
        if not sphutils.has_captcha_support() or get_current_user().is_authenticated:
            del self.fields['captcha']

    class Meta:
        model = WikiSnip
        exclude = ('name', 'group',)


def editSnip(request, group, snipName, versionId=None):
    version = None
    data = request.method == 'POST' and request.POST or None
    try:
        snip = WikiSnip.objects.get(group=group,
                                    name__exact=snipName)
        if versionId is not None:
            version = WikiSnipChange.objects.get(pk=versionId)
            if not version or version.snip != snip:
                # TODO: raise a 404 instead
                raise PermissionDenied()
            snip.body = version.body

        # SnipForm = forms.models.form_for_instance(snip, form = CaptchaEditBaseForm)
        form = WikiSnipForm(data, instance=snip)

    except WikiSnip.DoesNotExist:
        # SnipForm = forms.models.form_for_model(WikiSnip, form = CaptchaEditBaseForm)
        form = WikiSnipForm(data)
        snip = WikiSnip(name=snipName, group=group)
        # snip = None

    if not snip.has_edit_permission():
        raise PermissionDenied()

    # SnipForm.base_fields['body'].widget.attrs['cols'] = 80
    # SnipForm.base_fields['body'].widget.attrs['rows'] = 30

    changemessage = ""

    if request.method == 'POST':
        if 'type' in request.POST and request.POST['type'] == 'preview':
            return HttpResponse(str(WikiSnip(body=request.POST['body']).render()))
        changemessage = request.POST['message']
        # form = SnipForm(request.POST)

        if form.is_valid():
            old_title = None
            old_body = None
            change_type = 0
            if snip.id:
                old_title = snip.title
                old_body = snip.body

            snip = form.save(commit=False)
            snip.group = group
            snip.name = snipName
            if request.user.is_authenticated:
                snip.editor = request.user
            else:
                snip.editor = None
            snip.save()

            if old_body is not None:
                if snip.body != old_body:
                    change_type |= 1

                if snip.title != old_title:
                    change_type |= 2

            else:
                # if a snip is new, everything has changed ..
                change_type = 1 | 2 | 4

            data = form.cleaned_data

            if tag_set_labels(snip, data['tags']):
                change_type |= 4

            change = WikiSnipChange(snip=snip,
                                    # editor = request.user,
                                    editor=snip.editor,
                                    edited=datetime.today(),
                                    message=request.POST['message'],
                                    title=snip.title,
                                    body=snip.body,
                                    change_type=change_type,
                                    )
            change.save()

            tag_set_labels(change, data['tags'])

            return HttpResponseRedirect(snip.get_absolute_url())

    else:
        # form = SnipForm()

        if snip is not None:
            form.fields['tags'].initial = tag_get_labels(snip)
        pass

    if version:
        from sphene.community.templatetags.sph_extras import sph_date
        changemessage = ugettext('Reverted to revision of %(editdate)s') % {'editdate': sph_date(version.edited)}

    return render(request,
                  'sphene/sphwiki/editSnip.html',
                  {'form': form,
                   'snip': snip,
                   'version': version,
                   'changemessage': changemessage})


class TagSnipListView(ListView):
    template_name = 'sphene/sphwiki/list_tag_snips.html'
    # paginate_by = 50
    allow_empty = True
    tag: Tag

    # noinspection PyMethodOverriding
    def get(self, request, group, tag_name, *args, **kwargs):
        self.tag = get_object_or_404(Tag, group=group, name__exact=tag_name)
        self.extra_context = {'tag_name': self.tag.name}
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return tag_get_models_by_tag(WikiSnip.objects.all(), self.tag)

    