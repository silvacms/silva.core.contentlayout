
import uuid
import logging

from five import grok
from zope.component import getMultiAdapter
from zope.interface import Interface, implementedBy
from zope.interface.interfaces import ISpecification
from zeam import component

from Products.Silva.icon import registry as icon_registry

from ..interfaces import IBlockManager, IBoundBlockManager, IBlockController
from ..interfaces import IBlockConfigurations, IBlockConfiguration, IBlock

_marker = object()
logger = logging.getLogger('silva.core.contentlayout')


class Block(object):
    grok.baseclass()
    grok.implements(IBlock)


class BlockConfiguration(object):
    grok.provides(IBlockConfiguration)

    def __init__(self, block):
        self.identifier = grok.name.bind().get(block)
        self.title = grok.title.bind().get(block)
        self.block = block

    def get_icon(self, view):
        icon = None
        try:
            icon = icon_registry.get_icon_by_identifier(
                ('silva.core.contentlayout.blocks', self.identifier))
        except ValueError:
            return None
        return '/'.join((view.root_url, icon))

    def is_available(self, view):
        context = grok.context.bind(default=None).get(self.block)
        if context is not None:
            if not ISpecification.providedBy(context):
                context = implementedBy(context)
            return context.providedBy(view.context)
        return True


class BlockConfigurations(component.Component):
    grok.provides(IBlockConfigurations)
    grok.adapts(IBlock, Interface)

    def __init__(self, block, context):
        self.block = block
        self.context = context

    def get_by_identifier(self, identifier=None):
        return BlockConfiguration(self.block)

    def get_all(self):
        return [self.get_by_identifier()]


class BlockController(grok.MultiAdapter):
    grok.baseclass()
    grok.provides(IBlockController)

    def __init__(self, block, context, request):
        self.block = block
        self.context = context
        self.request = request

    def editable(self):
        return False

    def indexes(self):
        return []

    def fulltext(self):
        return []

    def remove(self):
        pass

    def render(self):
        raise NotImplementedError


class BoundBlockManager(grok.MultiAdapter):
    grok.adapts(Interface, Interface)
    grok.provides(IBoundBlockManager)

    def __init__(self, context, request):
        self.manager = IBlockManager(context)
        self.context = context
        self.request = request

    def add(self, slot_id, block, index=0):
        return self.manager.add(slot_id, block, index=index)

    def move(self, slot_id, block_id, index=0):
        return self.manager.move(slot_id, block_id, index=index)

    def remove(self, block_id):
        block, controller = self.get(block_id)
        if block is None:
            return False
        controller.remove()
        return self.manager.remove(block_id)

    def replace(self, block_id, new_block):
        block, controller = self.get(block_id)
        if block is None:
            return False
        controller.remove()
        return self.manager.replace(block_id, new_block)

    def get(self, block_id):
        block = self.manager.get_block(block_id)
        if block is not None:
            return block, getMultiAdapter(
                (block, self.context, self.request),
                IBlockController)
        return None, None

    def visit(self, function):
        for block_id, block in self.manager.get_all():
            controller = getMultiAdapter(
                (block, self.context, self.request), IBlockController)
            function(block_id, controller)

    def render(self, slot_id):
        for block_id, block in self.manager.get_slot(slot_id):
            if block is not None:
                controller = getMultiAdapter(
                    (block, self.context, self.request), IBlockController)
                yield {"block_id": block_id,
                       "block_editable": controller.editable() and 'true',
                       "block_data": controller.render()}
            else:
                logger.error(u'Missing block %s in document.' % block_id)



class BlockManager(grok.Annotation):
    grok.context(Interface)
    grok.implements(IBlockManager)
    grok.provides(IBlockManager)

    def __init__(self):
        super(BlockManager, self).__init__()
        self._blocks = {}
        self._slot_to_block = {}
        self._block_to_slot = {}

    def add(self, slot_id, block, index=0):
        if slot_id not in self._slot_to_block:
            self._slot_to_block[slot_id] = []
        block_id = str(uuid.uuid1())
        self._slot_to_block[slot_id].insert(index, block_id)
        self._block_to_slot[block_id] = slot_id
        self._blocks[block_id] = block
        self._p_changed = True
        return block_id

    def move(self, slot_id, block_id, index):
        previous_slot_id = self._block_to_slot[block_id]
        self._block_to_slot[block_id] = slot_id
        self._slot_to_block[previous_slot_id].remove(block_id)
        if slot_id not in self._slot_to_block:
            self._slot_to_block[slot_id] = []
        self._slot_to_block[slot_id].insert(index, block_id)
        self._p_changed = True
        return previous_slot_id

    def remove(self, block_id):
        slot_id = self._block_to_slot.get(block_id, _marker)
        if slot_id is not _marker:
            self._slot_to_block[slot_id].remove(block_id)
            del self._block_to_slot[block_id]
        del self._blocks[block_id]
        self._p_changed = True
        return True

    def replace(self, block_id, new_block):
        self._blocks[block_id] = new_block
        self._p_changed = True
        return True

    def get_block(self, block_id):
        return self._blocks.get(block_id)

    def get_slot(self, slot_id):
        return map(lambda block_id: (block_id, self._blocks.get(block_id)),
                   self._slot_to_block.get(slot_id, []))

    def get_all(self):
        return list(self._blocks.iteritems())
