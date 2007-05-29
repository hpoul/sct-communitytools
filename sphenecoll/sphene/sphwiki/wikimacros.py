from django.views.generic.list_detail import object_list
from django import template

from sphene.community.sphutils import HTML
from sphene.community.middleware import get_current_request

from sphene.sphwiki.models import WikiAttachment

class AttachmentListMacro (object):
    """ Displays a list of attachments for a macro. """

    def __init__(self, snip):
        self.snip = snip

    def handleMacroCall(self, doc, params):
        templateName = params.get('template', 'sphene/sphwiki/macros/_attachment_list.html')

        attachments = WikiAttachment.objects.filter( snip = self.snip )

        res = object_list( request = get_current_request(),
                           queryset = attachments,
                           template_name = templateName,
                           extra_context = { 'snip': self.snip, },
                           allow_empty = True,
                           template_object_name = 'attachment',
                           )

        return HTML(res.content)

class AttachmentMacro (object):
    """ Displays a download link for a given attachment. """

    def __init__(self, snip):
        self.snip = snip

    def handleMacroCall(self, doc, params):
        if not 'id' in params:
            return doc.createTextNode("Error, no 'category' or 'template' given for news macro.")


        templateName = params.get('template', 'sphene/sphwiki/macros/_attachment.html')
        try:
            attachment = WikiAttachment.objects.get( pk = params['id'] )
        except WikiAttachment.DoesNotExist:
            return HTML( '<b>Attachment does not exist: %s</b>' % params['id'] )

        t = template.loader.get_template( templateName )
        c = template.Context( { 'attachment': attachment,
                                'params': params,
                                }
                              )

        return HTML( t.render(c) )

class ImageMacro (object):
    def handleMacroCall(self, doc, params):
        if params.has_key( 'id' ):
            attachment = WikiAttachment.objects.get( id = params['id'] )
            el = doc.createElement( 'img' )
            el.setAttribute( 'src', attachment.get_fileupload_url() )
            for paramName in [ 'width', 'height', 'alt', 'align' ]:
                if params.has_key( paramName ):
                    el.setAttribute( paramName, params[paramName] )
            return el
        return doc.createTextNode("Error, no 'id' given for img macro.")

