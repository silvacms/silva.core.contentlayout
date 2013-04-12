# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import logging

from five import grok
from zope.interface import Interface

from silva.core.editor.transform.silvaxml.xmlexport import TextProducerProxy
from zeam.component.site import getWrapper

from Products.SilvaExternalSources.interfaces import IExternalSourceManager
from Products.SilvaExternalSources.errors import SourceError
from Products.SilvaExternalSources.silvaxml.xmlexport import \
    SourceParametersProducer
from silva.core.xml import producers, NS_SILVA_URI

from . import NS_LAYOUT_URI
from .. import interfaces
from ..blocks.slot import BlockSlot
from ..blocks.source import SourceBlock
from ..blocks.text import TextBlock
from ..interfaces import IPageModelVersion
from ..slots.restrictions import BlockAll, CodeSourceName,Content


logger = logging.getLogger('silva.core.xml')


class BasePageProducer(producers.SilvaProducer):
    grok.adapts(interfaces.IPage, Interface)
    grok.baseclass()

    def sax_design(self):
        design = self.context.get_design()
        if design is not None:
            attrs = {}
            if IPageModelVersion.providedBy(design):
                # XXX extern
                attrs['path'] = self.get_path_to(design)
            else:
                attrs['id'] = design.get_design_identifier()
            self.startElementNS(NS_LAYOUT_URI, 'design', attrs)
            manager = interfaces.IBlockManager(self.context)
            for slot_id in manager.get_slot_ids():
                self.startElementNS(NS_LAYOUT_URI, 'slot', {'id': slot_id})
                for block_id, block in manager.get_slot(slot_id):
                    self.subsax(block, parent=self)
                self.endElementNS(NS_LAYOUT_URI, 'slot')
            self.endElementNS(NS_LAYOUT_URI, 'design')


class BlockProducer(producers.SilvaProducer):
    grok.adapts(interfaces.IBlock, Interface)

    def sax(self, parent):
        raise NotImplementedError('no xml producer defined for block type %s'
            % self.context.__class__.__name__)


class ReferenceBlockProducer(producers.SilvaProducer):
    grok.adapts(interfaces.IReferenceBlock, Interface)

    def sax(self, parent):
        self.startElementNS(
            NS_LAYOUT_URI, 'referenceblock',
            {'target': parent.get_reference(self.context.identifier)})
        self.endElementNS(NS_LAYOUT_URI, 'referenceblock')


class SourceBlockProducer(producers.SilvaProducer, SourceParametersProducer):
    grok.adapts(SourceBlock, Interface)

    def sax(self, parent):
        exported = self.getExported()
        manager = getWrapper(parent.context, IExternalSourceManager)
        try:
            source = manager(
                exported.request, instance=self.context.identifier)
        except SourceError, error:
            exported.reportError(
                u"Broken source block in page while exporting: "
                u"{0}.".format(error),
                content=parent.context)
            return
        self.startElementNS(NS_LAYOUT_URI, 'sourceblock',
                            {"id": source.getSourceId()})
        self.sax_source_parameters(source)
        self.endElementNS(NS_LAYOUT_URI, 'sourceblock')


class TextBlockProducer(producers.SilvaProducer):
    grok.adapts(TextBlock, Interface)

    def sax(self, parent):
        self.startElementNS(NS_LAYOUT_URI, 'textblock', {
                'id': self.context.identifier})
        TextProducerProxy(parent.context, self.context).sax(self)
        self.endElementNS(NS_LAYOUT_URI, 'textblock')


class SlotBlockProducer(producers.SilvaProducer):
    grok.adapts(BlockSlot, Interface)

    def sax(self, parent):
        self.startElementNS(NS_LAYOUT_URI, 'slotblock', {
                'id': self.context.identifier,
                'css_class': self.context.css_class,
                'tag': self.context.tag})
        restrictions = self.context.get_restrictions()
        if restrictions:
            self.startElementNS(NS_LAYOUT_URI, 'restrictions')
            for restriction in restrictions:
                self.subsax(restriction)
            self.endElementNS(NS_LAYOUT_URI, 'restrictions')
        self.endElementNS(NS_LAYOUT_URI, 'slotblock')


class PageModel(producers.SilvaVersionedContentProducer):
    grok.adapts(interfaces.IPageModel, Interface)

    def sax(self):
        self.startElementNS(NS_LAYOUT_URI, 'page_model', {
                'id': self.context.id})
        self.sax_workflow()
        self.sax_versions()
        self.endElementNS(NS_LAYOUT_URI, 'page_model')


class PageModelVersionProducer(BasePageProducer):
    grok.adapts(interfaces.IPageModelVersion, Interface)

    def sax(self):
        self.startElementNS(
            NS_SILVA_URI, 'content', {'version_id': self.context.id})
        self.sax_metadata()
        self.sax_design()
        self.endElementNS(NS_SILVA_URI, 'content')


class CodeSourceNameRestriction(producers.SilvaProducer):
    grok.adapts(CodeSourceName, Interface)

    def sax(self):
        self.startElementNS(NS_LAYOUT_URI, 'codesourcename-restriction')
        for name in self.context.allowed:
            self.startElementNS(NS_LAYOUT_URI, 'allowed', {'name': name})
            self.endElementNS(NS_LAYOUT_URI, 'allowed')
        for name in self.context.disallowed:
            self.startElementNS(NS_LAYOUT_URI, 'disallowed', {'name': name})
            self.endElementNS(NS_LAYOUT_URI, 'disallowed')
        self.endElementNS(NS_LAYOUT_URI, 'codesourcename-restriction')


class ContentRestrictionProvider(producers.SilvaProducer):
    grok.adapts(Content, Interface)

    def sax(self):
        self.startElementNS(
            NS_LAYOUT_URI, 'content-restriction', {'schema': self.get_schema()})
        self.endElementNS(NS_LAYOUT_URI, 'content-restriction')

    def get_schema(self):
        return ":".join([self.context.schema.__module__,
                         self.context.schema.__name__])


class BlockAllRestrictionProducer(producers.SilvaProducer):
    grok.adapts(BlockAll, Interface)

    def sax(self):
        self.startElementNS(NS_LAYOUT_URI, 'blockall-restriction')
        self.endElementNS(NS_LAYOUT_URI, 'blockall-restriction')

