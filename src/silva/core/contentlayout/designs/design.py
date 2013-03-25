# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from Acquisition import aq_base

from five import grok
from chameleon.zpt.template import PageTemplateFile
from chameleon.tales import PythonExpr
from chameleon.tales import StringExpr
from chameleon.tales import NotExpr
from chameleon.tales import ExistsExpr
from chameleon.tales import StructureExpr
from z3c.pt.expressions import PathExpr, ProviderExpr
from zope.interface import Interface, alsoProvides, noLongerProvides
from zope.component import getUtility
from zope.event import notify

from silva.core.interfaces import IVersion
from silva.core.interfaces.errors import ContentError
from silva.fanstatic import need
from silva.translations import translate as _

from ..interfaces import IDesign, IDesignLookup, IPage, IEditionResources
from ..interfaces import IDesignAssociatedEvent, IDesignDeassociatedEvent
from ..interfaces import DesignAssociatedEvent, DesignDeassociatedEvent
from ..interfaces import ICachableDesign
from .expressions import SlotExpr


class TemplateFile(PageTemplateFile):
    # Use the chameleon default
    default_expression = 'python'

    expression_types = {
        'python': PythonExpr,
        'string': StringExpr,
        'not': NotExpr,
        'path': PathExpr,
        'provider': ProviderExpr,
        'exists': ExistsExpr,
        'structure': StructureExpr,
        'slot': SlotExpr,
        }


class Design(object):
    """A Design.
    """
    grok.implements(IDesign, ICachableDesign)
    grok.context(Interface)
    grok.provides(IDesign)
    grok.title('Template')
    grok.baseclass()

    template = None
    description = None
    slots = {}
    markers = []
    __template_path__ = 'inline'

    def __init__(self, content, request, stack):
        self.content = content
        self.request = request
        self.stack = stack
        self.edition = False

    @classmethod
    def get_design_identifier(cls):
        return grok.name.bind().get(cls)

    @classmethod
    def get_all_design_identifiers(cls, known=None):
        if known is None:
            known = []
        known.append(cls.get_design_identifier())
        return known

    @classmethod
    def get_design_title(cls):
        return grok.title.bind().get(cls)

    def default_namespace(self):
        namespace = {}
        namespace['design'] = self
        namespace['content'] = self.content
        namespace['request'] = self.request
        return namespace

    def namespace(self):
        return {}

    def update(self):
        pass

    def __call__(self, edition=False):
        __info__ = 'Rendering design: %s' % self.__template_path__
        self.update()
        namespace = {}
        namespace.update(self.default_namespace())
        namespace.update(self.namespace())
        if edition:
            need(IEditionResources)
            self.edition = True
        return self.template(**namespace)


class DesignAccessors(object):
    """ A mixin class to provide get/set design methods
    """
    _design_name = None

    def get_design(self):
        if hasattr(aq_base(self), '_v_design'):
            return self._v_design
        design = None
        if self._design_name is not None:
            service = getUtility(IDesignLookup)
            design = service.lookup_design_by_name(self._design_name)
            if ICachableDesign.providedBy(design):
                self._v_design = design
        return design

    def set_design(self, design):
        previous = self.get_design()
        if previous is None:
            previous_identifier = None
        else:
            previous_identifier = previous.get_design_identifier()
        if design is None:
            new_identifier = None
        else:
            new_identifier = design.get_design_identifier()
            # Check the new design is not using it self.
            if IDesign.providedBy(self):
                local_identifier = self.get_design_identifier()
                if local_identifier in design.get_all_design_identifiers():
                    raise ContentError(
                        _(u"This template cannot be used for this model"),
                        content=self.get_silva_object())

        if previous_identifier != new_identifier:
            # If there is a change
            if hasattr(aq_base(self), '_v_design'):
                del self._v_design

            if previous is not None:
                notify(DesignDeassociatedEvent(self, previous))
            # Change
            self._design_name = new_identifier
            if design is not None:
                notify(DesignAssociatedEvent(self, design))
        return design


@grok.subscribe(IPage, IDesignAssociatedEvent)
def set_markers(content, event):
    target = content
    if IVersion.providedBy(content):
        target = content.get_silva_object()
    for marker in event.design.markers:
        alsoProvides(target, marker)

@grok.subscribe(IPage, IDesignDeassociatedEvent)
def remove_markers(content, event):
    target = content
    if IVersion.providedBy(content):
        target = content.get_silva_object()
    for marker in event.design.markers:
        if marker.providedBy(target):
            noLongerProvides(target, marker)
