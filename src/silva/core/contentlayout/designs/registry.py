
from five import grok
from grokcore.component.util import sort_components
from zope.testing import cleanup
from zope.interface.interfaces import IInterface

from AccessControl.security import checkPermission

from silva.core.contentlayout.interfaces import IDesignLookup


class DesignRegistry(object):
    """Register designs
    """
    grok.implements(IDesignLookup)

    def __init__(self):
        self._designs = {}
        self._designs_by_name = {}

    def register(self, factory):
        context = grok.context.bind().get(factory)
        name = grok.name.bind().get(factory)
        if not name:
            raise ValueError('Design %r must defined a grok.name' % factory)
        if name in self._designs_by_name:
            raise ValueError(
                'Error while registering design %r, '
                'Design %r is already registered for name "%s"' %
                (factory, self._designs_by_name[name], name))
        self._designs_by_name[name] = factory
        factories = self._designs.setdefault(context, [])
        factories.append(factory)

    def remove(self, factory):
        self._designs

    def lookup_design(self, context):
        candidates = []
        for iface, factories in self._designs.iteritems():
            candidates.extend([factory for factory in factories
                               if self._is_allowed(factory, context)])
        return sort_components(candidates)

    def lookup_design_by_name(self, name):
        return self._designs_by_name.get(name)

    def default_design(self, context):
        return None

    def default_design_by_content_type(self, content_type, parent):
        return None

    def lookup_by_content_type(self, content_type, parent):
        return self.lookup_design(parent)

    def _is_allowed(self, design, context):
        required_context = grok.context.bind().get(design)
        if IInterface.providedBy(required_context):
            if not required_context.providedBy(context):
                return False
        elif not issubclass(context, required_context):
            return False

        permission = grok.require.bind().get(design)
        if permission:
            return checkPermission(permission, context)
        return True

    def clear(self):
        self._designs = {}


registry = DesignRegistry()
cleanup.addCleanUp(registry.clear)

grok.global_utility(
    registry,
    provides=IDesignLookup,
    direct=True)
