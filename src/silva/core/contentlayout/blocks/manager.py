
import uuid
import logging

from five import grok
from zope.component import getMultiAdapter
from zope.interface import Interface
from zeam import component

from Products.Silva.icon import registry as icon_registry

from ..interfaces import IBlockManager, IBlockController
from ..interfaces import IBlockFactories, IBlock

_marker = object()
logger = logging.getLogger('silva.core.contentlayout')


class Block(object):
    grok.baseclass()
    grok.implements(IBlock)


class BlockConfig(component.Component):
    component.provides(IBlockFactories)
    grok.adapts(IBlock, Interface)

    def __init__(self, factory, context):
        self.factory = factory
        self.context = context

    def get_by_identifier(self, _):
        name = grok.name.bind().get(self.factory)
        icon = None
        try:
            icon = icon_registry.get_icon_by_identifier(
                ('silva.core.contentlayout.blocks',
                 grok.name.bind().get(self.factory)))
        except ValueError:
            pass
        return {'name': name,
                'add': name,
                'title': grok.title.bind().get(self.factory),
                'icon': icon,
                'context': grok.context.bind(default=None).get(self.factory),
                'block': self.factory}

    def get_all(self):
        return [self.get_by_identifier(None)]


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


class BlockManager(grok.Annotation):
    grok.context(Interface)
    grok.implements(IBlockManager)
    grok.provides(IBlockManager)

    def __init__(self):
        super(BlockManager, self).__init__()
        self._blocks = {}
        self._slot_to_block = {}
        self._block_to_slot = {}

    def addable(self, slot_id, block_name, content):
        design = content.get_design()
        slot = design.slot[slot_id]
        factory, restriction = slot.get_block_type(block_name)
        if factory is not None:
            return True
        return False

    def add(self, slot_id, block, index=0):
        if slot_id not in self._slot_to_block:
            self._slot_to_block[slot_id] = []
        block_id = str(uuid.uuid1())
        self._slot_to_block[slot_id].insert(index, block_id)
        self._block_to_slot[block_id] = slot_id
        self._blocks[block_id] = block
        self._p_changed = True
        return block_id

    def movable(self, block_id, slot_id, content):
        block = self._blocks.get(block_id)
        design = content.get_design()
        slot = design.slots[slot_id]
        return slot.is_block_allowed(block, content)

    def move(self, block_id, slot_id, index, content):
        if not self.movable(block_id, slot_id, content):
            raise ValueError('Cannot move this block in this slot')
        block = self._blocks.get(block_id)
        if block is None or slot_id is None or index is None:
            raise ValueError("Invalid block id `%s`, slot `%s` "
                             "or index `%s`" %
                             (block_id, slot_id, index))
        previous_slot_id = self._block_to_slot[block_id]
        self._block_to_slot[block_id] = slot_id
        self._slot_to_block[previous_slot_id].remove(block_id)
        if slot_id not in self._slot_to_block:
            self._slot_to_block[slot_id] = []
        self._slot_to_block[slot_id].insert(index, block_id)
        self._p_changed = True
        return previous_slot_id

    def remove(self, block_id, content, request):
        block = self.get(block_id)
        if block is None:
            return False
        bound = getMultiAdapter((block, content, request), IBlockController)
        bound.remove()
        slot_id = self._block_to_slot.get(block_id, _marker)
        if slot_id is not _marker:
            self._slot_to_block[slot_id].remove(block_id)
            del self._block_to_slot[block_id]
        del self._blocks[block_id]
        self._p_changed = True
        return True

    def replace(self, block_id, new_block, content, request):
        block = self.get(block_id)
        if block is None:
            return False
        bound = getMultiAdapter((block, content, request), IBlockController)
        bound.remove()
        self._blocks[block_id] = new_block
        self._p_changed = True
        return True

    def get(self, block_id):
        return self._blocks.get(block_id)

    def visit(self, function, content, request):
        for block_id, block in self._blocks.iteritems():
            controller = getMultiAdapter(
                (block, content, request), IBlockController)
            function(block_id, controller)

    def render(self, slot_id, content, request):
        for block_id in self._slot_to_block.get(slot_id, []):
            block = self.get(block_id)
            if block is not None:
                controller = getMultiAdapter(
                    (block, content, request), IBlockController)
                yield {"block_id": block_id,
                       "block_editable": controller.editable() and 'true',
                       "block_data": controller.render()}
            else:
                logger.error(u'Missing block %s in document.' % block_id)
