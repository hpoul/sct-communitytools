
import markdown
import re

class MacrosExtension (markdown.Extension):
    def __init__(self, configs):
        self.config = {
            'macros': [ { }, 'hehe' ],
            }
        
        # Override defaults with user settings
        for key, value in configs :
            # self.config[key][0] = value
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        self.md = md

        MACROS_RE = r'''{(?P<macroName>\w+?)(?P<macroParams> .*)?}''';
        md.inlinePatterns.append(Macros(MACROS_RE, self.config))


class Macros (markdown.BasePattern):
    def __init__(self, pattern, config):
        markdown.BasePattern.__init__(self, pattern)
        self.config = config
        self.macros = self.config['macros'][0]

    def handleMatch(self, m, doc) :
        macroName = m.group('macroName')
        if self.macros.has_key( macroName ):
            macroParams = m.group('macroParams')
            allParams = dict()
            if macroParams is not None:
                paramRe = re.compile( '(?P<name>\w+?)=(?:"(?P<escapedValue>.*?)"|(?P<value>.+?))(?=\s|$)', re.S )
                for param in paramRe.finditer( macroParams ):
                    if param.group('escapedValue') is None:
                        value = param.group('value')
                    else:
                        value = param.group('escapedValue')
                    allParams[param.group('name')] = value
            return self.macros[macroName].handleMacroCall(doc, allParams)
        a = doc.createTextNode(m.group())
        return a

"""
Base class for all macros ...
"""
class Macro (object):
    pass

def makeExtension(configs=None) :
    return MacrosExtension(configs=configs)
