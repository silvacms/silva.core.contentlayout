# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import sys

from five import grok
from zope.publisher.browser import TestRequest


from Products.SilvaExternalSources.silvaxml.xmlimport import SourceHandler

from silva.core.xml import NS_SILVA_URI, handlers
from silva.core import conf as silvaconf
from silva.core.editor.transform.silvaxml import NS_EDITOR_URI
from silva.core.editor.transform.silvaxml.xmlimport import TextHandler
from zeam.component import getWrapper

from . import NS_LAYOUT_URI
from ..designs.registry import registry
from ..interfaces import IBlockManager, IBlockController
from ..blocks.slot import BlockSlot
from ..blocks.text import TextBlock
from ..blocks.contents import ReferenceBlock
from ..blocks.source import SourceBlock
from ..slots import restrictions


silvaconf.namespace(NS_LAYOUT_URI)


class SlotHandler(handlers.SilvaHandler):
    silvaconf.name('slot')

    def startElementNS(self, name, qname, attrs):
        if (NS_LAYOUT_URI, 'slot') == name:
            self.setResult(attrs[(None, 'id')])


class BlockHandler(handlers.SilvaHandler):
    grok.baseclass()

    def addBlock(self, block):
        slot_id = self.parent()
        context = self.parentHandler().parent()
        manager = IBlockManager(context)
        manager.add(slot_id, block, index=-1)

    # BBB
    add_block = addBlock


class ReferenceBlockHandler(BlockHandler):
    silvaconf.name('referenceblock')

    block = None

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'referenceblock'):
            path = attrs[(None, 'target')]
            block = ReferenceBlock()
            page = self.parentHandler().parent()
            self.block = block

            def set_target(target):
                controller = getWrapper(
                    (block, page, TestRequest()),
                    IBlockController)
                controller.content = target

            importer = self.getExtra()
            importer.resolveImportedPath(page, set_target, path)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'referenceblock'):
            if self.block is not None:
                self.addBlock(self.block)
                self.block = None


class SourceBlockHandler(SourceHandler, BlockHandler):
    silvaconf.name('sourceblock')

    block = None

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'sourceblock'):
            identifier = self.createSource(
                attrs[(None, 'id')],
                self.parentHandler().parent())
            if identifier is not None:
                self.block = SourceBlock(identifier)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'sourceblock'):
            if self.block is not None:
                self.addBlock(self.block)
                self.block = None


class AllowedCodeSourceNameHandler(handlers.SilvaHandler):

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'allowed'):
            name = attrs[(None, 'name')]
            self.parentHandler().restriction.allowed.add(name)
        if name == (NS_LAYOUT_URI, 'disallowed'):
            name = attrs[(None, 'name')]
            self.parentHandler().restriction.disallowed.add(name)


class CodeSourceNameRestrictionHandler(handlers.SilvaHandler):
    silvaconf.name('codesourcename-restriction')

    restriction = None

    def getOverrides(self):
        return {(NS_LAYOUT_URI, 'allowed'): AllowedCodeSourceNameHandler,
                (NS_LAYOUT_URI, 'disallowed'): AllowedCodeSourceNameHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'codesourcename-restriction'):
            self.restriction = restrictions.CodeSourceName()

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'codesourcename-restriction'):
            self.parentHandler().addRestriction(self.restriction)
            self.restriction = None


class ContentRestrictionHandler(handlers.SilvaHandler):
    silvaconf.name('content-restriction')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'content-restriction'):
            class_path = attrs[(None, 'schema')]
            module, name = class_path.split(':', 1)
            __import__(module)
            schema = getattr(sys.modules[module], name, None)
            if schema is None:
                raise ImportError('unable to import %s' % class_path)
            self.parentHandler().addRestriction(restrictions.Content(schema))


class BlockAllRestrictionHandler(handlers.SilvaHandler):
    silvaconf.name('blockall-restriction')

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'blockall-restriction'):
            self.parentHandler().addRestriction(restrictions.BlockAll())


class BlockSlotHandler(BlockHandler):
    silvaconf.name('slotblock')

    def addRestriction(self, restriction):
        restrictions = self.getData('restrictions')
        if restrictions is not None:
            restrictions.append(restriction)

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'slotblock'):
            for option in ('id', 'tag', 'css_class'):
                self.setData(option, attrs.get((None, option)))
            self.setData('restrictions', [])

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'slotblock'):
            self.addBlock(
                BlockSlot(
                    identifier=self.getData('id'),
                    css_class=self.getData('css_class'),
                    tag=self.getData('tag'),
                    restrictions=self.getData('restrictions')))
            self.clearData()


class TextBlockHandler(BlockHandler):
    silvaconf.name('textblock')

    block = None

    def getOverrides(self):
        return {(NS_EDITOR_URI, 'text'): TextHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'textblock'):
            self.block = TextBlock(attrs.get((None, 'id')))
            self.setResult(self.block)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'textblock'):
            if self.block is not None:
                self.addBlock(self.block)
                self.block = None


class DesignHandler(handlers.SilvaHandler):

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'design'):
            id = attrs.get((None, 'id'))
            page = self.parent()
            if id is not None:
                # XXX handle case when design is not here
                design = registry.lookup_design_by_name(id)
                page.set_design(design)
            else:
                path = attrs.get((None, 'path'))
                importer = self.getExtra()

                def set_design(design):
                    page.set_design(design)

                importer.resolveImportedPath(page, set_design, path)


class PageModelHandler(handlers.SilvaHandler):
    silvaconf.name('page_model')

    def getOverrides(self):
        return {(NS_SILVA_URI, 'content'): PageModelVersionHandler}

    def _createContent(self, identifier):
        factory = self.parent().manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel(identifier, '', no_default_version=True)

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'page_model'):
            self.createContent(attrs)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'page_model'):
            self.notifyImport()


class PageModelVersionHandler(handlers.SilvaVersionHandler):

    def getOverrides(self):
        return {(NS_LAYOUT_URI, 'design'): DesignHandler}

    def _createVersion(self, identifier):
        factory = self.parent().manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModelVersion(identifier, '')

    def startElementNS(self, name, qname, attrs):
        if (NS_SILVA_URI, 'content') == name:
            self.createVersion(attrs)

    def endElementNS(self, name, qname):
        if (NS_SILVA_URI, 'content') == name:
            self.updateVersionCount()
            self.storeMetadata()
            self.storeWorkflow()

