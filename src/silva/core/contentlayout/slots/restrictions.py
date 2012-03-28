from five import grok
from zope.interface.interfaces import IInterface
from zope.interface import Interface
from zope.component import getUtility
from silva.core.references.interfaces import IReferenceService

from silva.core.contentlayout import interfaces
from silva.core.contentlayout.blocks.source import SourceBlock
from silva.core.contentlayout.blocks.contents import ReferenceBlock


class SlotRestriction(object):
    """Base class for simple slot restrictions.
    """
    grok.baseclass()
    grok.implements(interfaces.ISlotRestriction)

    def allow_block_type(self, block_type):
        return True

    def allow_name(self, name):
        return True

    def allow_block(self, block, context, slot):
        return self.allow_block_type(block.__class__)

    def apply_to(self, block_type):
        context_required = grok.context.bind().get(self)
        if context_required is None:
            return False
        if IInterface.providedBy(context_required):
            if context_required.implementedBy(block_type):
                return True
        elif issubclass(block_type, context_required):
            return True
        return False


class BlockAll(SlotRestriction):
    grok.context(Interface)

    def allow_block_type(self, _):
        return False


class CodeSource(SlotRestriction):
    grok.context(SourceBlock)


class CodeSourceName(CodeSource):

    def __init__(self, *names):
        self._names = set(names)

    def allow_name(self, name):
        return name in self._names


class Content(SlotRestriction):
    grok.implements(interfaces.IContentSlotRestriction)
    grok.context(ReferenceBlock)

    interface = None

    def __init__(self, interface):
        self.interface = interface

    def allow_block(self, block, context, slot):
        if not super(Content, self).allow_block(block, context, slot):
            return False

        service = getUtility(IReferenceService)
        reference = service.get_reference(context, name=block.identifier)
        silva_content = reference.target

        if self.interface.providedBy(silva_content):
            return True
        return False
