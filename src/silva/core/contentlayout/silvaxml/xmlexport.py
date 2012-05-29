# -*- coding: utf-8 -*-
# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt


from five import grok
from zope.interface import Interface

from silva.core.editor.transform.silvaxml.xmlexport import TextProducerProxy
from Products.Silva.silvaxml import xmlexport, NS_SILVA_URI
from .. import interfaces
from ..blocks.source import SourceBlock
from ..blocks.text import TextBlock
from ..blocks.slot import BlockSlot
from . import NS_URI

from silva.core.contentlayout.interfaces import IPageModelVersion
from silva.core.contentlayout.slots.restrictions import BlockAll, CodeSourceName,\
    Content


class BasePageProducer(xmlexport.SilvaProducer):
    grok.adapts(interfaces.IPage, Interface)
    grok.baseclass()

    def design(self):
        design = self.context.get_design()
        if design is not None:
            attrs = {}
            if IPageModelVersion.providedBy(design):
                attrs['path'] = self.relative_path_to(design)
            else:
                attrs['id'] = design.get_identifier()
            self.startElementNS(NS_URI, 'design', attrs)
            manager = interfaces.IBlockManager(self.context)
            for slot_id in manager.get_slot_ids():
                self.startElementNS(NS_URI, 'slot', {'id': slot_id})
                for block_id, block in manager.get_slot(slot_id):
                    self.subsax(block, parent=self)
                self.endElementNS(NS_URI, 'slot')
            self.endElementNS(NS_URI, 'design')


class BlockProducer(xmlexport.SilvaProducer):
    grok.adapts(interfaces.IBlock, Interface)

    def sax(self, parent):
        raise NotImplementedError('no xml producer defined for block type %s'
            % self.context.__class__.__name__)


class ReferenceBlockProducer(xmlexport.SilvaProducer):
    grok.adapts(interfaces.IReferenceBlock, Interface)

    def sax(self, parent):
        self.startElementNS(NS_URI, 'referenceblock',
            {'ref': parent.reference(self.context.identifier)})
        self.endElementNS(NS_URI, 'referenceblock')


class SourceBlockProducer(xmlexport.SilvaProducer):
    grok.adapts(SourceBlock, Interface)

    def sax(self, parent):
        self.startElementNS(NS_URI, 'sourceblock',
            {"id": self.context.identifier})
        self.endElementNS(NS_URI, 'sourceblock')


class TextBlockProducer(xmlexport.SilvaProducer):
    grok.adapts(TextBlock, Interface)

    def sax(self, parent):
        self.startElementNS(NS_URI, 'textblock')
        TextProducerProxy(parent.context, self.context).sax(self)
        self.endElementNS(NS_URI, 'textblock')


class SlotBlockProducer(xmlexport.SilvaProducer):
    grok.adapts(BlockSlot, Interface)

    def sax(self, parent):
        self.startElementNS(NS_URI, 'slotblock',
            {'css_class': self.context.css_class,
             'tag': self.context.tag})
        restrictions = self.context._restrictions
        if restrictions:
            self.startElementNS(NS_URI, 'restrictions')
            for restriction in restrictions:
                self.subsax(restriction)
            self.endElementNS(NS_URI, 'restrictions')
        self.endElementNS(NS_URI, 'slotblock')


class PageModel(xmlexport.SilvaVersionedContentProducer):
    grok.adapts(interfaces.IPageModel, Interface)

    def sax(self):
        self.startElementNS(NS_URI, 'pagemodel',
            {'id': self.context.id})
        self.workflow()
        self.versions()
        self.endElementNS(NS_URI, 'pagemodel')


class PageModelVersionProducer(BasePageProducer):
    grok.adapts(interfaces.IPageModelVersion, Interface)

    def sax(self):
        self.startElementNS(NS_SILVA_URI, 'content', {'version_id': self.context.id})
        self.metadata()
        self.design()
        self.endElementNS(NS_SILVA_URI, 'content')


class CodeSourceNameRestriction(xmlexport.SilvaBaseProducer):
    grok.adapts(CodeSourceName, Interface)

    def sax(self):
        self.startElementNS(NS_URI, 'codesourcename-restriction')
        for name in self.context.allowed:
            self.startElementNS(NS_URI, 'allowed', {'name': name})
            self.endElementNS(NS_URI, 'allowed')
        for name in self.context.disallowed:
            self.startElementNS(NS_URI, 'disallowed', {'name': name})
            self.endElementNS(NS_URI, 'disallowed')
        self.endElementNS(NS_URI, 'codesourcename-restriction')


class ContentRestrictionProvider(xmlexport.SilvaBaseProducer):
    grok.adapts(Content, Interface)

    def sax(self):
        self.startElementNS(NS_URI, 'content-restriction',
                            {'schema': self.get_schema()})
        self.endElementNS(NS_URI, 'content-restriction')

    def get_schema(self):
        return ":".join([self.context.schema.__module__,
                         self.context.schema.__name__])


class BlockAllRestrictionProducer(xmlexport.SilvaBaseProducer):
    grok.adapts(BlockAll, Interface)

    def sax(self):
        self.startElementNS(NS_URI, 'blockall-restriction')
        self.endElementNS(NS_URI, 'blockall-restriction')

