
import uuid
import logging

from five import grok
from zope.component import getMultiAdapter

from silva.core.interfaces import IDataManager, IVersion
from silva.core.contentlayout.interfaces import IBlockManager

_marker = object()
logger = logging.getLogger('silva.core.contentlayout')


class Block(object):
    grok.baseclass()


class BlockManager(grok.Annotation):
    grok.context(IVersion)
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

    def move(self, block_id, slot_id=None, index=None):
        pass

    def remove(self, block_id, content, request):
        block = self.get(block_id)
        if block is None:
            return False
        bound = getMultiAdapter((block, content, request), IDataManager)
        bound.clear()
        slot_id = self._block_to_slot.get(block_id, _marker)
        if slot_id is not _marker:
            self._slot_to_block.remove(block_id)
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
                bound = getMultiAdapter((block, content, request), IDataManager)
                yield {"block_id": block_id, "html": bound.render()}
            else:
                logger.error(u'Missing block %s in document.' % block_id)
