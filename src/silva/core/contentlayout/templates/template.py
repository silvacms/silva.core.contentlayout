
from five import grok
from chameleon.zpt.template import PageTemplateFile
from chameleon.tales import PythonExpr
from chameleon.tales import StringExpr
from chameleon.tales import NotExpr
from chameleon.tales import ExistsExpr
from chameleon.tales import StructureExpr
from z3c.pt.expressions import PathExpr, ProviderExpr
from zope.interface import Interface, alsoProvides, noLongerProvides

from silva.core.interfaces import IVersion
from silva.core.contentlayout.templates.expressions import SlotExpr
from silva.core.contentlayout.interfaces import ITemplate, IPage
from silva.core.contentlayout.interfaces import (ITemplateAssociatedEvent,
                                                 ITemplateDeassociatedEvent)


class TemplateFile(PageTemplateFile):
    # Use the chameleon default
    default_expression = 'python'

    expression_types = {
        'python': PythonExpr,
        'string': StringExpr,
        'not': NotExpr,
        'path': PathExpr,
        'provider': ProviderExpr,
        'exists': ExistsExpr,
        'structure': StructureExpr,
        'slot': SlotExpr,
        }


class Template(object):
    """A Template.
    """
    grok.implements(ITemplate)
    grok.context(Interface)
    grok.provides(ITemplate)
    grok.baseclass()

    template = None
    __template_path__ = 'inline'

    @classmethod
    def get_identifier(cls):
        return grok.name.bind().get(cls)

    def __init__(self, content, request):
        self.content = content
        self.request = request

    def default_namespace(self):
        namespace = {}
        namespace['template'] = self
        namespace['content'] = self.content
        namespace['request'] = self.request
        return namespace

    def namespace(self):
        return {}

    def update(self):
        pass

    def __call__(self):
        __info__ = 'Rendering template: %s' % self.__template_path__
        self.update()
        namespace = {}
        namespace.update(self.default_namespace())
        namespace.update(self.namespace())
        return self.template(**namespace)


@grok.subscribe(IPage, ITemplateAssociatedEvent)
def set_markers(content, event):
    target = content
    if IVersion.providedBy(content):
        target = content.get_content()
    if hasattr(event.template, 'markers'):
        alsoProvides(target, event.template.markers)

@grok.subscribe(IPage, ITemplateDeassociatedEvent)
def remove_markers(content, event):
    target = content
    if IVersion.providedBy(content):
        target = content.get_content()
    if hasattr(event.template, 'markers'):
        noLongerProvides(target, event.template.markers)
