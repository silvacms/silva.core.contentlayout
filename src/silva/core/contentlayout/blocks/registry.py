# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from grokcore.component.util import _sort_key
from zope.interface import implementedBy
from zope.testing import cleanup

from zeam.component import getComponent
from ..interfaces import IBlock, IBlockConfigurations, IBlockLookup


def get_block_configuration(factory, context):
    component = getComponent(
        (implementedBy(factory), context),
        IBlockConfigurations)
    return component(factory, context)


class BlockRegistry(object):
    """Register available block types.
    """
    grok.implements(IBlockLookup)

    def __init__(self):
        self._blocks = {}

    def register_block(self, name, factory):
        assert IBlock.implementedBy(factory)
        name = name.encode('utf-8')
        if name in self._blocks:
            raise ValueError(u'Duplicate block type "%s".' % name)
        self._blocks[name] = factory

    def lookup_block(self, context):
        candidates = []
        for factory in sorted(self._blocks.itervalues(), key=_sort_key):
            candidates.extend(get_block_configuration(
                    factory, context).get_all())
        return candidates

    def lookup_block_by_name(self, context, name):
        parts = name.split(':', 1)
        factory = self._blocks[parts[0]]
        if factory is not None:
            identifier = len(parts) > 1 and parts[1] or None
            return get_block_configuration(
                factory, context).get_by_identifier(identifier)
        return None

    def clear(self):
        self._blocks = {}


registry = BlockRegistry()
cleanup.addCleanUp(registry.clear)
