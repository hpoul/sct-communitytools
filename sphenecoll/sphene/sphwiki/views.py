from django import newforms as forms
from django.newforms import widgets
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.template import loader
from django.template.context import RequestContext
from django import newforms as forms
from django.newforms import widgets
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings

from datetime import datetime
from difflib import ndiff, HtmlDiff
from urllib import quote

from sphene.sphwiki import wikimacros
from sphene.sphwiki.models import WikiSnip, WikiSnipChange, WikiAttachment
from sphene.community import PermissionDenied, sphutils
from sphene.community.sphutils import get_sph_setting
from sphene.community.middleware import get_current_sphdata, get_current_user

import os

# Create your views here.


def showSnip(request, group, snipName):
    snip_rendered_body = None
    try:
        snip = WikiSnip.objects.get( group = group,
                                     name__exact = snipName )
    except WikiSnip.DoesNotExist:
        snip = WikiSnip( name = snipName, group = group )

    if not snip.has_view_permission():
        raise PermissionDenied()

    res = None
    if 'type' in request.GET:
        if request.GET['type'] == 'src':
            res =  HttpResponse( snip.body, mimetype = 'text/plain', )
        if request.GET['type'] == 'full':
            res = HttpResponse( snip.render(), mimetype = 'text/html', )

    if not res:
        sphdata = get_current_sphdata()
        snip_rendered_body = False
        redirects = ()
        while not snip_rendered_body or 'sphwiki_redirect_to_snip' in sphdata:
            if snip_rendered_body:
                if snip in redirects:
                    request.user.message_set.create( message = "Detected redirect loop." )
                    break
                redirects += (snip,)
                snip = sphdata['sphwiki_redirect_to_snip']
                del sphdata['sphwiki_redirect_to_snip']
            snip_rendered_body = snip.render()
            
        if sphdata != None: sphdata['subtitle'] = snip.title or snip.name
    
        res = render_to_response( 'sphene/sphwiki/showSnip.html',
                                  { 'snip': snip,
                                    'snipName' : snipName,
                                    'snip_rendered_body': snip_rendered_body,
                                    'redirects': redirects,
                                    },
                                  context_instance = RequestContext(request) )

    res.sph_lastmodified = snip.changed
    return res


def generatePDF(request, group, snipName):
    if not hasattr(settings, 'SPH_SETTINGS'):
        return HttpResponse( 'Not configured.' )

    snip = get_object_or_404( WikiSnip,
                              group = group,
                              name = snipName )


    try:
        contents = open(snip.pdf_get(), 'rb').read()
    except Exception, e:
        return HttpResponse('Error while generating PDF file. %s' % str(e))

    response = HttpResponse(contents, mimetype='application/pdf')
    
    
    return response

def history(request, group, snipName):
    snip = get_object_or_404( WikiSnip,
                              group = group,
                              name = snipName )
    return object_list( request = request,
                        queryset = snip.wikisnipchange_set.order_by('-edited'),
                        template_name = 'sphene/sphwiki/history.html',
                        allow_empty = True,
                        extra_context = { 'snipName': snipName,
                                          'snip': snip,
                                          },
                        )

def recentChanges(request, group):
    res =  object_list( request = request,
                        queryset = WikiSnipChange.objects.filter( snip__group = group ).order_by('-edited'),
                        template_name = 'sphene/sphwiki/recentChanges.html',
                        allow_empty = True,
                        )
    res.sph_lastmodified = True
    return res

def diff(request, group, snipName, changeId = None):
    snip = get_object_or_404( WikiSnip,
                              group = group,
                              name = snipName )
    changeEnd = get_object_or_404( WikiSnipChange,
                                   snip = snip,
                                   pk = changeId, )
    args = { 'snip': snip,
             'snipName': snipName,}
    try:
        changeStart = snip.wikisnipchange_set.filter( edited__lt = changeEnd.edited, ).order_by('-edited')[0]
        args['prev_change'] = changeStart
    except IndexError:
        changeStart = None
        diffTable = "This is the first change."

    try:
        next_change = snip.wikisnipchange_set.filter( edited__gt = changeEnd.edited, ).order_by('edited')[0]
        args['next_change'] = next_change
    except IndexError:
        pass

    if changeStart:
        htmlDiff = HtmlDiff(wrapcolumn = 50,)
        from sphene.community.templatetags.sph_extras import sph_date, sph_fullusername
        diffTable = htmlDiff.make_table( changeStart.body.splitlines(1),
                                         changeEnd.body.splitlines(1),
                                         fromdesc = sph_date( changeStart.edited ) + ' by ' + sph_fullusername( changeStart.editor ),
                                         todesc = sph_date( changeEnd.edited ) + ' by ' + sph_fullusername( changeEnd.editor ),
                                         context = True, )

    args['diffTable'] = diffTable
    return render_to_response( 'sphene/sphwiki/diff.html',
                               args,
                               context_instance = RequestContext(request) )

    
def attachment(request, group, snipName):
    snip = WikiSnip.objects.get( name__exact = snipName, group = group )
    res = WikiAttachment.objects.filter( snip = snip )
    return object_list( request = request,
                        queryset = WikiAttachment.objects.filter( snip = snip ),
                        template_name = 'sphene/sphwiki/listAttachments.html',
                        extra_context = { 'snipName': snipName,
                                          'snip': snip,
                                          },
                        allow_empty = True )

def attachmentEdit(request, group, snipName, attachmentId = None):
    attachment = None
    if attachmentId is None:
        AttachmentForm = forms.models.form_for_model( WikiAttachment )
    else:
        attachment = WikiAttachment.objects.get(id=attachmentId)
        AttachmentForm = forms.models.form_for_instance(attachment)

    if attachment:
        if not attachment.snip.has_edit_permission():
            raise PermissionDenied()
    if 'delete' in request.GET and request.GET['delete'] == '1':
        attachment.delete()
        request.user.message_set.create( message = "Successfully deleted attachment." )
        return HttpResponseRedirect( attachment.snip.get_absolute_attachmenturl() )

    AttachmentForm.base_fields['fileupload'].widget = widgets.FileInput()

    if request.method == 'POST':
        reqdata = request.POST.copy()
        reqdata.update(request.FILES)
        form = AttachmentForm(reqdata)
        if form.is_valid():
            attachment = form.save(commit=False)
            snip = WikiSnip.objects.get( name__exact = snipName )
            attachment.snip = snip
            attachment.uploader = request.user
            attachment.save_fileupload_file( reqdata['fileupload']['filename'], reqdata['fileupload']['content'] )
            attachment.save()
            return HttpResponseRedirect( snip.get_absolute_attachmenturl() )
    else:
        form = AttachmentForm()

    return render_to_response( 'sphene/sphwiki/editAttachment.html',
                               { 'form': form,
                                 'snipName' : snipName,
                                 },
                               context_instance = RequestContext(request) )


class CaptchaEditBaseForm(forms.BaseForm):
    """ BaseForm which displays a captcha, if required. """

    def __init__(self, *args, **kwargs):
        super(CaptchaEditBaseForm, self).__init__(*args, **kwargs)
        
        if sphutils.has_captcha_support() and not get_current_user().is_authenticated():
            self.fields['captcha'] = sphutils.CaptchaField(widget=sphutils.CaptchaWidget,
                                                           help_text = 'Please enter the result of the above calculation.',
                                                           )


def editSnip(request, group, snipName):
    original_body = None
    try:
        snip = WikiSnip.objects.get( group = group,
                                     name__exact = snipName )
        original_body = snip.body
        SnipForm = forms.models.form_for_instance(snip, form = CaptchaEditBaseForm)
    except WikiSnip.DoesNotExist:
        SnipForm = forms.models.form_for_model(WikiSnip, form = CaptchaEditBaseForm)
        snip = WikiSnip( name = snipName, group = group )
        #snip = None

    if not snip.has_edit_permission():
        raise PermissionDenied()

    SnipForm.base_fields['body'].widget.attrs['cols'] = 80
    SnipForm.base_fields['body'].widget.attrs['rows'] = 30


    if request.method == 'POST':
        if 'type' in request.POST and request.POST['type'] == 'preview':
            return HttpResponse( WikiSnip(body = request.POST['body']).render() )
        form = SnipForm(request.POST)
        if form.is_valid():
            snip = form.save(commit=False)
            snip.group = group
            snip.name = snipName
            snip.editor = request.user
            snip.save()

            change = WikiSnipChange( snip = snip,
                                     editor = request.user,
                                     edited = datetime.today(),
                                     message = request.POST['message'],
                                     body = snip.body,
                                     )
            change.save()
            
            return HttpResponseRedirect( snip.get_absolute_url() )

    else:
        form = SnipForm()

    t = loader.get_template( 'sphene/sphwiki/editSnip.html' )
    return HttpResponse( t.render( RequestContext( request, { 'form': form, 'snip': snip } ) ) )
