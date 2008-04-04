
from django.template import TemplateDoesNotExist
from django.template.context import RequestContext
from django.template.loader import render_to_string

from sphene.sphblockframework.blockregistry import Block



class NavigationBlock(Block):

    name = 'sphnavigationblock'
    label = 'Navigation'
    requires_configuration = True

    def render(self):
        return "Not yet implemented."


class UserBlock(Block):

    name = 'sphuserblock'
    label = 'User'
    requires_configuration = False


    def render(self):
        request = self.get_request()
        user = self.get_user()
        return render_to_string('sphene/sphblockframework/blocks/userblock.html',
                                dictionary={ 'user': user, },
                                context_instance=RequestContext(request),)


class RenderTemplateBlock(Block):

    name = 'sphrendertemplate'
    label = 'Render Template'
    requires_configuration = True

    def render(self):
        request = self.get_request()
        try:
            return render_to_string(self.block_position. \
                                        block_configuration.config_value,
                                    context_instance = RequestContext(request))
        except TemplateDoesNotExist, e:
            return 'Template does not exist.'


