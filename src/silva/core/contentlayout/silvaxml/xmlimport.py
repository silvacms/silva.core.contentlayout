# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

import sys

from five import grok
from zope.publisher.browser import TestRequest


from Products.SilvaExternalSources.interfaces import IExternalSourceManager
from Products.SilvaExternalSources.silvaxml import NS_SOURCE_URI
from Products.SilvaExternalSources.silvaxml.xmlimport import \
    SourceParametersHandler

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

    def add_block(self, block):
        slot_id = self.parent()
        context = self.parentHandler().parent()
        manager = IBlockManager(context)
        manager.add(slot_id, block, index=-1)
        self.setResult(block)


class ReferenceBlockHandler(BlockHandler):
    silvaconf.name('referenceblock')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'referenceblock'):
            path = attrs[(None, 'ref')]
            block = ReferenceBlock()
            page = self.parentHandler().parent()
            importer = self.getExtra()
            self._block = block

            def set_target(target):
                controller = getWrapper(
                    (block, page, TestRequest()),
                    IBlockController)
                controller.content = target

            importer.resolveImportedPath(page, set_target, path)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'referenceblock'):
            self.add_block(self._block)
            self._block = None


class SourceBlockHandler(BlockHandler):
    silvaconf.name('sourceblock')

    source = None

    def getOverrides(self):
        return {(NS_SOURCE_URI, 'fields'): SourceParametersHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'sourceblock'):
            request = self.getExtra().request
            manager = getWrapper(self.parentHandler().parent(),
                                 IExternalSourceManager)
            identifier = attrs[(None, 'id')]
            self.source = manager(request, name=identifier)
            instance_identifier = self.source.new()
            self._block = SourceBlock(instance_identifier)
            self.setResult(self.source)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'sourceblock'):
            self.add_block(self._block)
            self.source = None
            del self._block


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

    def getOverrides(self):
        return {(NS_LAYOUT_URI, 'allowed'): AllowedCodeSourceNameHandler,
                (NS_LAYOUT_URI, 'disallowed'): AllowedCodeSourceNameHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'codesourcename-restriction'):
            self.restriction = restrictions.CodeSourceName()

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'codesourcename-restriction'):
            self.parent()._restrictions.append(self.restriction)
            del self.restriction


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
            self.parent()._restrictions.append(restrictions.Content(schema))


class BlockAllRestrictionHandler(handlers.SilvaHandler):
    silvaconf.name('blockall-restriction')

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'blockall-restriction'):
            self.parent()._restrictions.append(restrictions.BlockAll())


class BlockSlotHandler(BlockHandler):
    silvaconf.name('slotblock')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'slotblock'):
            options = {}
            # XXX: handle restrictions
            for option_name in ('tag', 'css_class'):
                value = attrs.get((None, option_name))
                if value is not None:
                    options[option_name] = value

            self.block = BlockSlot(**options)
            self.setResult(self.block)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'slotblock'):
            self.add_block(self.block)
            del self.block


class TextBlockHandler(BlockHandler):
    silvaconf.name('textblock')

    def getOverrides(self):
        return {(NS_EDITOR_URI, 'text'): TextHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'textblock'):
            identifier = attrs[(None, 'identifier')]
            self.block = TextBlock(identifier)
            self.setResult(self.block)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'textblock'):
            self.add_block(self.block)
            del self.block


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
    silvaconf.name('pagemodel')

    def getOverrides(self):
        return {(NS_SILVA_URI, 'content'): PageModelVersionHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_LAYOUT_URI, 'pagemodel'):
            uid = self.generateIdentifier(attrs)
            factory = self.parent().manage_addProduct[
                'silva.core.contentlayout']
            factory.manage_addPageModel(uid, '', no_default_version=True)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_LAYOUT_URI, 'pagemodel'):
            self.notifyImport()


class PageModelVersionHandler(handlers.SilvaVersionHandler):

    def getOverrides(self):
        return {(NS_LAYOUT_URI, 'design'): DesignHandler}

    def startElementNS(self, name, qname, attrs):
        if (NS_SILVA_URI, 'content') == name:
            uid = attrs[(None, 'version_id')].encode('utf-8')
            factory = self.parent().manage_addProduct[
                'silva.core.contentlayout']
            factory.manage_addPageModelVersion(uid, '')
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if (NS_SILVA_URI, 'content') == name:
            self.updateVersionCount()
            self.storeMetadata()
            self.storeWorkflow()

