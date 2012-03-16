
from five import grok
from grokcore.component.util import sort_components
from zope.testing import cleanup

from AccessControl.security import checkPermission

from silva.core.contentlayout.interfaces import ITemplateLookup


class TemplateRegistry(grok.GlobalUtility):
    """Register templates
    """
    grok.implements(ITemplateLookup)

    def __init__(self):
        self._templates = {}

    def register(self, factory):
        context = grok.context.bind().get(factory)
        factories = self._templates.setdefault(context, [])
        factories.append(factory)

    def lookup(self, context):
        candidates = []
        for iface, factories in self._templates.iteritems():
            candidates.extend([factory for factory in factories
                               if self._is_allowed(factory, context)])
        return sort_components(candidates)

    def _is_allowed(self, template, context):
        permission = grok.require.bind().get(template)
        if permission:
            return checkPermission(permission, context)
        return True

    def clear(self):
        self._templates = {}


registry = TemplateRegistry()
cleanup.addCleanUp(registry.clear)

# grok.global_utility(
#     registry,
#     provides=ITemplateLookup,
#     direct=True)
