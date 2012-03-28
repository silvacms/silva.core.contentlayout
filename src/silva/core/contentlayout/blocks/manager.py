
import uuid
import logging

from five import grok
from zope.component import getMultiAdapter
from zope.interface import Interface

from ..interfaces import IBlockManager, IBlockController, IBlock

_marker = object()
logger = logging.getLogger('silva.core.contentlayout')


class Block(object):
    grok.implements(IBlock)
    grok.baseclass()


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

    def can_move(self, block_id, slot_id=None):
        return True

    def move(self, block_id, slot_id=None, index=None):
        block = self._blocks.get(block_id)
        if block is None or slot_id is None or index is None:
            raise ValueError("couldn't find block with id `%s`" % block_id)
        previous_slot_id = self._block_to_slot[block_id]
        self._block_to_slot[block_id] = slot_id
        self._slot_to_block[previous_slot_id].remove(block_id)
        self._slot_to_block[slot_id].insert(index or -1, block_id)
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
                bound = getMultiAdapter(
                    (block, content, request), IBlockController)
                yield {"block_id": block_id, "html": bound.render()}
            else:
                logger.error(u'Missing block %s in document.' % block_id)
