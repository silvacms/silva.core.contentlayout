
from five import grok
from grokcore.component.util import _sort_key
from zope.interface import implementedBy
from zope.interface.interfaces import ISpecification
from zope.testing import cleanup


from zeam.component import getComponent
from ..interfaces import IBlock, IBlockFactories



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


    def all_new(self, context):

        def get_factories(factory):
            component = getComponent(
                (implementedBy(factory), context),
                IBlockFactories, default=None)
            if component is None:
                return []
            return component(factory, context)

        candidates = []
        for factory in self._blocks.itervalues():
            candidates.extend(get_factories(factory))
        return candidates

    def lookup(self, name):
        return self._blocks.get(name)

    def all(self, context=None):
        candidates = [
            (name, factory) for name, factory in self._blocks.iteritems()
            if self._check(factory, context)]
        return sorted(candidates, key=lambda (n, f): _sort_key(f))

    def clear(self):
        self._blocks = {}

    def _check(self, factory, context):
        if context is None:
            return True
        requires = grok.context.bind(default=None).get(factory)
        if requires is None:
            return True
        if not ISpecification.providedBy(requires):
            requires = implementedBy(requires)
        return requires.providedBy(context)


registry = BlockRegistry()
cleanup.addCleanUp(registry.clear)
