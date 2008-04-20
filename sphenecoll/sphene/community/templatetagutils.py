
from django import template


class SimpleRetrieverNode(template.Node):
    def __init__(self, nodelist, retrievervar, callback):
        self.nodelist = nodelist
        self.retrievervar = retrievervar
        self.callback = callback

    def render(self, context):
        retriever = self.retrievervar.resolve(context)
        context.push()
        self.callback(retriever, context)
        output = self.nodelist.render(context)
        context.pop()
        return output

def simple_retriever_tag(parser, token, tagname, callback):
    bits = list(token.split_contents())
    if len(bits) != 2:
        raise template.TemplateSyntaxError("%r requires a variable as first argument." % bits[0])

    retrievevar = parser.compile_filter(bits[1])
    nodelist = parser.parse(('end'+tagname,))
    parser.delete_first_token()
    return SimpleRetrieverNode(nodelist, retrievevar, callback)
