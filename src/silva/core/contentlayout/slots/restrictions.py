# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from AccessControl.security import checkPermission

from five import grok
from zope.interface.interfaces import IInterface
from zope.interface import Interface

from .. import interfaces
from ..blocks.source import SourceBlock
from ..blocks.contents import ReferenceBlock


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
        requires = grok.context.bind(default=None).get(self)
        if requires is None:
            return False
        if IInterface.providedBy(requires):
            if requires.implementedBy(block_type):
                return True
        elif issubclass(block_type, requires):
            return True
        return False


class BlockAll(SlotRestriction):
    """Block any type of block not already authorized.
    """
    grok.context(Interface)

    def allow_configuration(self, configuration, slot, context):
        return False

    def allow_controller(self, controller, slot, context):
        return False

    def apply_to(self, block_type):
        return True


class CodeSource(SlotRestriction):
    """Block code source type block.
    """
    grok.context(SourceBlock)


class CodeSourceName(CodeSource):
    """Block a block of code source type based on the identifier of
    selected or desired code source.
    """

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


class Permission(SlotRestriction):
    """Block any type of block based on a permission that the editor
    must have.
    """
    grok.context(Interface)

    permission = None

    def __init__(self, permission='silva.ChangeSilvaContent'):
        self.permission = permission

    def allow_configuration(self, configuration, slot, context):
        if checkPermission(self.permission, context):
            return None
        return False

    def allow_controller(self, controller, slot, context):
        if checkPermission(self.permission, context):
            return None
        return False

    def apply_to(self, block_type):
        return True


class Content(SlotRestriction):
    """Block a block of content type based on the interface of the
    selected or desired linked content.
    """
    grok.implements(interfaces.IContentSlotRestriction)
    grok.context(ReferenceBlock)

    schema = None

    def __init__(self, schema=interfaces.IBlockable):
        self.schema = schema

    def allow_controller(self, controller, context, slot):
        if self.schema.providedBy(controller.content):
            return True
        return False
