
import uuid
import logging

from five import grok
from zope.component import getMultiAdapter
from zope.interface import Interface

from ..interfaces import IBlockManager, IBlockController, IBlock

_marker = object()
logger = logging.getLogger('silva.core.contentlayout')


class Block(object):
    grok.baseclass()
    grok.implements(IBlock)


class BlockController(grok.MultiAdapter):
    grok.baseclass()
    grok.provides(IBlockController)

    def __init__(self, block, context, request):
        self.block = block
        self.context = context
        self.request = request

    def editable(self):
        return False

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

    def new(self, slot_id, block):
        if slot_id not in self._slot_to_block:
            self._slot_to_block[slot_id] = []
        block_id = str(uuid.uuid1())
        self._slot_to_block[slot_id].append(block_id)
        self._block_to_slot[block_id] = slot_id
        self._blocks[block_id] = block
        self._p_changed = True
        return block_id

    def can_move(self, block_id, context, slot_id):
        block = self._blocks.get(block_id)
        template = context.get_template()
        slot = template.slots[slot_id]
        return slot.is_block_allowed(block, context)

    def move(self, block_id, context, slot_id, index):
        if not self.can_move(block_id, context, slot_id):
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

    def get(self, block_id):
        return self._blocks.get(block_id)

    def render(self, slot_id, content, request):
        for block_id in self._slot_to_block.get(slot_id, []):
            block = self.get(block_id)
            if block is not None:
                controller = getMultiAdapter(
                    (block, content, request), IBlockController)
                yield {"block_id": block_id,
                       "block_editable": controller.editable() and 'true',
                       "html": controller.render()}
            else:
                logger.error(u'Missing block %s in document.' % block_id)
