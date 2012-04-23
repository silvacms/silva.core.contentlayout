
from five import grok
from chameleon.zpt.template import PageTemplateFile
from chameleon.tales import PythonExpr
from chameleon.tales import StringExpr
from chameleon.tales import NotExpr
from chameleon.tales import ExistsExpr
from chameleon.tales import StructureExpr
from z3c.pt.expressions import PathExpr, ProviderExpr
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.component import getUtility
from zope.event import notify

from silva.core.interfaces import IVersion
from silva.fanstatic import need

from ..interfaces import IDesign, IDesignLookup, IPage, IEditionResources
from ..interfaces import IDesignAssociatedEvent, IDesignDeassociatedEvent
from ..interfaces import DesignAssociatedEvent, DesignDeassociatedEvent
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

    def __init__(self, content, request, stack):
        self.content = content
        self.request = request
        self.stack = stack
        self.edition = False

    @classmethod
    def get_identifier(cls):
        return grok.name.bind().get(cls)

    @classmethod
    def get_title(cls):
        return grok.title.bind().get(cls)

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

    def __call__(self, edition=False):
        __info__ = 'Rendering design: %s' % self.__template_path__
        self.update()
        namespace = {}
        namespace.update(self.default_namespace())
        namespace.update(self.namespace())
        if edition:
            need(IEditionResources)
            self.edition = True
        return self.template(**namespace)


class DesignAccessors(object):
    """ A mixin class to provide get/set design methods
    """

    _design_name = None

    def get_design(self):
        service = getUtility(IDesignLookup)
        if self._design_name is not None:
            return service.lookup_design_by_name(self._design_name)
        return None

    def set_design(self, design):
        previous = self.get_design()
        if design is None:
            identifier = None
        else:
            identifier = design.get_identifier()
        self._design_name = identifier
        if previous != design:
            if previous is not None:
                notify(DesignDeassociatedEvent(self, previous))
            if design is not None:
                notify(DesignAssociatedEvent(self, design))
        return design


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
