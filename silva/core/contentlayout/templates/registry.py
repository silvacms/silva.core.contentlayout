
from five import grok
from grokcore.component.util import sort_components
from zope.testing import cleanup


class TemplateRegistry(object):
    """Register templates
    """

    def __init__(self):
        self._templates = {}

    def register(self, factory):
        context = grok.context.bind().get(factory)
        factories = self._templates.setdefault(context, [])
        factories.append(factory)

    def lookup(self, context):
        candidates = []
        for iface, factories in self._templates.iteritems():
            candidates.extend(factories)
        return sort_components(candidates)

    def clear(self):
        self._templates = {}


registry = TemplateRegistry()
cleanup.addCleanUp(registry.clear)
