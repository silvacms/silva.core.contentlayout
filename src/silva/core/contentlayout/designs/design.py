
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

from ..interfaces import IDesign, IPage
from ..interfaces import IDesignAssociatedEvent, IDesignDeassociatedEvent
from .expressions import SlotExpr


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


class Design(object):
    """A Design.
    """
    grok.implements(IDesign)
    grok.context(Interface)
    grok.provides(IDesign)
    grok.title('Design')
    grok.baseclass()

    template = None
    description = None
    markers = []
    __template_path__ = 'inline'

    @classmethod
    def get_identifier(cls):
        return grok.name.bind().get(cls)

    @classmethod
    def get_title(cls):
        return grok.title.bind().get(cls)

    def __init__(self, content, request):
        self.content = content
        self.request = request

    def default_namespace(self):
        namespace = {}
        namespace['design'] = self
        namespace['content'] = self.content
        namespace['request'] = self.request
        return namespace

    def namespace(self):
        return {}

    def update(self):
        pass

    def __call__(self):
        __info__ = 'Rendering design: %s' % self.__template_path__
        self.update()
        namespace = {}
        namespace.update(self.default_namespace())
        namespace.update(self.namespace())
        return self.template(**namespace)


@grok.subscribe(IPage, IDesignAssociatedEvent)
def set_markers(content, event):
    target = content
    if IVersion.providedBy(content):
        target = content.get_content()
    for marker in event.design.markers:
        alsoProvides(target, marker)

@grok.subscribe(IPage, IDesignDeassociatedEvent)
def remove_markers(content, event):
    target = content
    if IVersion.providedBy(content):
        target = content.get_content()
    for marker in event.design.markers:
        if marker.providedBy(target):
            noLongerProvides(target, marker)
