
from five import grok
from zope.interface.interfaces import IInterface

from silva.core.contentlayout.interfaces import IBlock
from zope.testing import cleanup


class BlockRegistry(object):
    """Register available block types.
    """

    def __init__(self):
        self._blocks = {}

    def register(self, name, factory):
        assert IBlock.implementedBy(factory)
        name = name.encode('utf-8')
        if name in self._blocks:
            raise ValueError(u'Duplicate block type "%s".' % name)
        self._blocks[name] = factory

    def lookup(self, name):
        return self._blocks.get(name)

    def all(self, context=None):
        return [(name, factory) for name, factory in self._blocks.iteritems()
                if self._context_filter(context, factory)]

    def clear(self):
        self._blocks = {}

    def _context_filter(self, context, factory):
        if context is None:
            return True
        required_context = grok.context.bind().get(factory)
        if required_context is None:
            return True
        if IInterface.providedBy(required_context):
            return required_context.providedBy(context)
        return isinstance(context, required_context)


registry = BlockRegistry()
cleanup.addCleanUp(registry.clear)
