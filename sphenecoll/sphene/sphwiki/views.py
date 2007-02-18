from django import newforms as forms
from django.newforms import widgets
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.template import loader
from django.template.context import RequestContext
from django import newforms as forms
from django.newforms import widgets
from django.http import HttpResponse, HttpResponseRedirect


from sphene.sphwiki.models import WikiSnip, WikiAttachment


# Create your views here.


def showSnip(request, group, snipName):
    try:
        snip = WikiSnip.objects.get( group = group,
                                     name__exact = snipName )
    except WikiSnip.DoesNotExist:
        snip = None
    return render_to_response( 'sphene/sphwiki/showSnip.html',
                               { 'snip': snip,
                                 'snipName' : snipName,
                                 },
                               context_instance = RequestContext(request) )

def attachment(request, group, snipName):
    snip = WikiSnip.objects.get( name__exact = snipName, group = group )
    res = WikiAttachment.objects.filter( snip = snip )
    return object_list( request = request,
                        queryset = WikiAttachment.objects.filter( snip = snip ),
                        template_name = 'sphene/sphwiki/listAttachments.html',
                        extra_context = { 'snipName': snipName
                                          },
                        allow_empty = True )

def attachmentEdit(request, group, snipName, attachmentId = None):
    if attachmentId is None:
        AttachmentForm = forms.models.form_for_model( WikiAttachment )
    else:
        attachment = WikiAttachment.objects.get(id=attachmentId)
        AttachmentForm = forms.models.form_for_instance(attachment)

    AttachmentForm.base_fields['fileupload'].widget = widgets.FileInput()

    if request.method == 'POST':
        reqdata = request.POST.copy()
        reqdata.update(request.FILES)
        form = AttachmentForm(reqdata)
        if form.is_valid():
            attachment = form.save(commit=False)
            print "filename: %s" % reqdata['fileupload']['filename']
            snip = WikiSnip.objects.get( name__exact = snipName )
            attachment.snip = snip
            attachment.uploader = request.user
            attachment.save_fileupload_file( reqdata['fileupload']['filename'], reqdata['fileupload']['content'] )
            attachment.save()
            return HttpResponseRedirect( '../../../attachments/%s/' % snipName )
    else:
        form = AttachmentForm()

    return render_to_response( 'sphene/sphwiki/editAttachment.html',
                               { 'form': form,
                                 'snipName' : snipName,
                                 },
                               context_instance = RequestContext(request) )

def editSnip(request, group, snipName):
    try:
        snip = WikiSnip.objects.get( group = group,
                                     name__exact = snipName )
        SnipForm = forms.models.form_for_instance(snip)
    except WikiSnip.DoesNotExist:
        SnipForm = forms.models.form_for_model(WikiSnip)
        snip = None
    SnipForm.base_fields['body'].widget.attrs['cols'] = 80
    SnipForm.base_fields['body'].widget.attrs['rows'] = 30

    if request.method == 'POST':
        form = SnipForm(request.POST)
        if form.is_valid():
            snip = form.save(commit=False)
            snip.group = group
            snip.name = snipName
            snip.editor = request.user
            snip.save()
            return HttpResponseRedirect( '../../show/%s/' % snip.name )

    else:
        form = SnipForm()

    t = loader.get_template( 'sphene/sphwiki/editSnip.html' )
    return HttpResponse( t.render( RequestContext( request, { 'form': form } ) ) )
