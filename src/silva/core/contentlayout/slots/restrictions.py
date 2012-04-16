from five import grok
from zope.interface.interfaces import IInterface
from zope.interface import Interface

from silva.core.contentlayout import interfaces
from silva.core.contentlayout.blocks.source import SourceBlock
from silva.core.contentlayout.blocks.contents import ReferenceBlock


class SlotRestriction(object):
    """Base class for simple slot restrictions.
    """
    grok.baseclass()
    grok.implements(interfaces.ISlotRestriction)

    def allow_configuration(self, configuration, slot, context):
        return True

    def allow_controller(self, controller, slot, context):
        return True

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

    def allow_configuration(self, configuration, slot, context):
        return False

    def allow_controller(self, controller, slot, context):
        return False


class CodeSource(SlotRestriction):
    grok.context(SourceBlock)


class CodeSourceName(CodeSource):

    def __init__(self, allowed=set(), disallowed=set()):
        self.allowed = set(allowed)
        self.disallowed = set(disallowed)

    def allow_configuration(self, configuration, slot, context):
        return self._allow_identifier(configuration.source.id)

    def allow_controller(self, controller, slot, context):
        return self._allow_identifier(controller.source.id)

    def _allow_identifier(self, identifier):
        if self.allowed:
            return identifier in self.allowed
        return identifier not in self.disallowed


class Content(SlotRestriction):
    grok.implements(interfaces.IContentSlotRestriction)
    grok.context(ReferenceBlock)

    schema = None

    def __init__(self, schema=interfaces.IBlockable):
        self.schema = schema

    def allow_controller(self, controller, context, slot):
        if self.schema.providedBy(controller.content):
            return True
        return False
