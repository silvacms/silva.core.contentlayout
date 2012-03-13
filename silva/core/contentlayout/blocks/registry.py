
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

    def all(self):
        return self._blocks.items()

    def clear(self):
        self._blocks = {}


registry = BlockRegistry()
cleanup.addCleanUp(registry.clear)
