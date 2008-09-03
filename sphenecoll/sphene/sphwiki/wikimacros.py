from django.views.generic.list_detail import object_list
from django import template

from sphene.contrib.libs.markdown import mdx_macros
from sphene.community.sphsettings import get_sph_setting
from sphene.community.sphutils import HTML
from sphene.community.middleware import get_current_request, get_current_sphdata, get_current_group
from sphene.community.templatetags.sph_extras import resize

from sphene.sphwiki.models import WikiAttachment, WikiSnip

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
            try:
                attachment = WikiAttachment.objects.get( id = params['id'] )
            except WikiAttachment.DoesNotExist:
                return HTML( '<b>Attachment for image does not exist: %s</b>' % params['id'] )
            el = doc.createElement( 'img' )
            el.setAttribute( 'src', attachment.fileupload.url )

            cssclass = get_sph_setting('getwiki_macros_default_image_class')
            if cssclass is not None:
                el.setAttribute('class', cssclass)

            for paramName in [ 'class', 'width', 'height', 'alt', 'align' ]:
                if params.has_key( paramName ):
                    el.setAttribute( paramName, params[paramName] )

            if params.has_key('resize'):
                size = params['resize']
                width, height = size.split('x')
                src, width, height = resize(attachment.fileupload, size)
                el.setAttribute('src', src)
                el.setAttribute('width', '%dpx' % width)
                el.setAttribute('height', '%dpx' % height)

            # Create a link to view the image maximized.
            if not 'nolink' in params or not params['nolink']:
                el.setAttribute( 'border', '0' )
                a = doc.createElement( 'a' )
                a.setAttribute( 'href', attachment.fileupload.url )

                if cssclass is not None:
                    a.setAttribute('class', cssclass)

                a.appendChild(el)
                el = a

            return el
        return doc.createTextNode("Error, no 'id' given for img macro.")

class RedirectMacro (mdx_macros.PreprocessorMacro):
    """ Redirects the user from one wiki snip to another.
    This allows to create aliases for snip names. """

    def handlePreprocessorMacroCall(self, params):
        if not params.has_key( 'snip' ):
            return 'No "snip" parameter given to redirect macro.'

        sphdata = get_current_sphdata()
        snipName = params['snip'];
        try:
            snip = WikiSnip.objects.get( group = get_current_group(),
                                         name = snipName )
        except WikiSnip.DoesNotExist:
            return '**Wiki snip "%s" does not exist.**' % snipName

        request = get_current_request()
        if 'redirect' in request.GET and request.GET['redirect'] == 'no':
            return '**Redirect to "%s" disabled.**' % snipName
        
        sphdata['sphwiki_redirect_to_snip'] = snip
        
        return "**Redirecting to %s ...**" % snipName

