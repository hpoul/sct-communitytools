from django import newforms as forms
from django.newforms import widgets
from django.shortcuts import render_to_response, get_object_or_404
from django.views.generic.list_detail import object_list
from django.template import loader
from django.template.context import RequestContext
from django import newforms as forms
from django.newforms import widgets
from django.http import HttpResponse, HttpResponseRedirect

from datetime import datetime
from difflib import ndiff, HtmlDiff

from sphene.sphwiki.models import WikiSnip, WikiSnipChange, WikiAttachment
from sphene.community.templatetags.sph_extras import sph_markdown
from sphene.community import PermissionDenied
from sphene.community.middleware import get_current_sphdata

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

    if 'type' in request.GET:
        if request.GET['type'] == 'src':
            return HttpResponse( snip.body, mimetype = 'text/plain', )
	if request.GET['type'] == 'full':
	    return HttpResponse( sph_markdown(snip.body), mimetype = 'text/html', )

    snip_rendered_body = sph_markdown(snip.body) # TODO do this in the model ? like the board post body ?
    sphdata = get_current_sphdata()
    if sphdata != None: sphdata['subtitle'] = snip.title or snip.name
    
    return render_to_response( 'sphene/sphwiki/showSnip.html',
                               { 'snip': snip,
                                 'snipName' : snipName,
                                 'snip_rendered_body': snip_rendered_body,
                                 },
                               context_instance = RequestContext(request) )

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
    return object_list( request = request,
                        queryset = WikiSnipChange.objects.filter( snip__group = group ).order_by('-edited'),
                        template_name = 'sphene/sphwiki/recentChanges.html',
                        allow_empty = True,
                        )

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
    original_body = None
    try:
        snip = WikiSnip.objects.get( group = group,
                                     name__exact = snipName )
        original_body = snip.body
        SnipForm = forms.models.form_for_instance(snip)
    except WikiSnip.DoesNotExist:
        SnipForm = forms.models.form_for_model(WikiSnip)
        snip = WikiSnip( name = snipName, group = group )
        #snip = None

    if not snip.has_edit_permission():
        raise PermissionDenied()
    
    SnipForm.base_fields['body'].widget.attrs['cols'] = 80
    SnipForm.base_fields['body'].widget.attrs['rows'] = 30

    if request.method == 'POST':
        if 'type' in request.POST and request.POST['type'] == 'preview':
            return HttpResponse( sph_markdown(request.POST['body']) )
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
