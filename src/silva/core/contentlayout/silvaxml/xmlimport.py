
import sys
import lxml.sax

from five import grok
from zope.component import getMultiAdapter

from Products.Silva.silvaxml import xmlimport, NS_SILVA_URI
from zope.publisher.browser import TestRequest
from silva.core import conf as silvaconf
from silva.core.editor.transform.silvaxml import NS_EDITOR_URI
from silva.core.editor.transform.silvaxml.xmlimport import TextHandler
from ..designs.registry import registry
from ..interfaces import IBlockManager, IBlockController
from ..blocks.slot import BlockSlot
from ..blocks.text import TextBlock
from ..blocks.contents import ReferenceBlock
from ..slots import restrictions


from . import NS_URI
from zeam.form.silva.interfaces import IXMLFormSerialization
from Products.SilvaExternalSources.interfaces import IExternalSourceManager
from zeam.component import getWrapper
from Products.SilvaExternalSources.silvaxml import NS_SOURCE_URI
from silva.core.contentlayout.blocks.source import SourceBlock


silvaconf.namespace(NS_URI)


class SlotHandler(xmlimport.SilvaBaseHandler):
    silvaconf.name('slot')

    def startElementNS(self, name, qname, attrs):
        if (NS_URI, 'slot') == name:
            self.setResult(attrs[(None, 'id')])


class BlockHandler(xmlimport.SilvaBaseHandler):
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
        if name == (NS_URI, 'referenceblock'):
            path = attrs[(None, 'ref')]
            block = ReferenceBlock()
            self._block = block

            def set_target(target):
                controller = getMultiAdapter(
                    (block, self.parentHandler().parent(), TestRequest()),
                    IBlockController)
                controller.content = target

            info = self.getInfo()
            info.addAction(xmlimport.resolve_path, [set_target, info, path])

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'referenceblock'):
            self.add_block(self._block)
            self._block = None


class SourceFieldHandler(xmlimport.SilvaBaseHandler):

    proxy = None
    field_id = None

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SOURCE_URI, 'field'):
            self.proxy = lxml.sax.ElementTreeContentHandler()
            self.proxy.startElementNS(name, qname, attrs)
            self.field_id = attrs[(None, 'id')]
        elif self.proxy is not None:
            self.proxy.startElementNS(name, qname, attrs)

    def characters(self, input_text):
        text = input_text.strip()
        if self.proxy is not None and text:
            self.proxy.characters(text)

    def endElementNS(self, name, qname):
        if name == (NS_SOURCE_URI, 'field'):
            self.proxy.endElementNS(name, qname)
            deserializer = self.parentHandler().deserializers[self.field_id]
            deserializer(self.proxy.etree.getroot(), self.parentHandler())
            del self.proxy
        elif self.proxy is not None:
            self.proxy.endElementNS(name, qname)


class SourceFieldsHandler(xmlimport.SilvaBaseHandler):

    def getOverrides(self):
        return {(NS_SOURCE_URI, 'field'): SourceFieldHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_SOURCE_URI, 'fields'):
            self.deserializers = getWrapper(
                self.parent(),
                IXMLFormSerialization).getDeserializers()

    def endElementNS(self, name, qname):
        if name == (NS_SOURCE_URI, 'fields'):
            del self.deserializers


class SourceBlockHandler(BlockHandler):
    silvaconf.name('sourceblock')

    def getOverrides(self):
        return {(NS_SOURCE_URI, 'fields'): SourceFieldsHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'sourceblock'):
            request = self.getInfo().request
            manager = getWrapper(self.parentHandler().parent(),
                                 IExternalSourceManager)
            identifier = attrs[(None, 'id')]
            self._source = manager(request, name=identifier)
            instance_identifier = self._source.new()
            self._block = SourceBlock(instance_identifier)
            self.setResult(self._source)

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'sourceblock'):
            self.add_block(self._block)
            del self._source
            del self._block


class AllowedCodeSourceNameHandler(xmlimport.SilvaBaseHandler):

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'allowed'):
            name = attrs[(None, 'name')]
            self.parentHandler().restriction.allowed.add(name)
        if name == (NS_URI, 'disallowed'):
            name = attrs[(None, 'name')]
            self.parentHandler().restriction.disallowed.add(name)


class CodeSourceNameRestrictionHandler(xmlimport.SilvaBaseHandler):
    silvaconf.name('codesourcename-restriction')

    def getOverrides(self):
        return {(NS_URI, 'allowed'): AllowedCodeSourceNameHandler,
                (NS_URI, 'disallowed'): AllowedCodeSourceNameHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'codesourcename-restriction'):
            self.restriction = restrictions.CodeSourceName()

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'codesourcename-restriction'):
            self.parent()._restrictions.append(self.restriction)
            del self.restriction


class ContentRestrictionHandler(xmlimport.SilvaBaseHandler):
    silvaconf.name('content-restriction')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'content-restriction'):
            class_path = attrs[(None, 'schema')]
            module, name = class_path.split(':', 1)
            __import__(module)
            schema = getattr(sys.modules[module], name, None)
            if schema is None:
                raise ImportError('unable to import %s' % class_path)
            self.parent()._restrictions.append(restrictions.Content(schema))


class BlockAllRestrictionHandler(xmlimport.SilvaBaseHandler):
    silvaconf.name('blockall-restriction')

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'blockall-restriction'):
            self.parent()._restrictions.append(restrictions.BlockAll())


class BlockSlotHandler(BlockHandler):
    silvaconf.name('slotblock')

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'slotblock'):
            options = {}
            # XXX: handle restrictions
            for option_name in ('tag', 'css_class'):
                value = attrs.get((None, option_name))
                if value is not None:
                    options[option_name] = value

            self.block = BlockSlot(**options)
            self.setResult(self.block)

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'slotblock'):
            self.add_block(self.block)
            del self.block


class TextBlockHandler(BlockHandler):
    silvaconf.name('textblock')

    def getOverrides(self):
        return {(NS_EDITOR_URI, 'text'): TextHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'textblock'):
            self.block = TextBlock()
            self.setResult(self.block)

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'textblock'):
            self.add_block(self.block)
            del self.block


class DesignHandler(xmlimport.SilvaBaseHandler):

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'design'):
            id = attrs.get((None, 'id'))
            design = registry.lookup_design_by_name(id)
            if id is not None:
                self.parent().set_design(design)
            else:
                path = attrs.get((None, 'path'))
                if path is not None:
                    info = self.getInfo()
                    content = self.parent()

                    def set_design(design):
                        content.set_design(design)

                    info.addAction(
                        xmlimport.resolve_path, [set_design, info, path])


class PageModelHandler(xmlimport.SilvaBaseHandler):
    silvaconf.name('pagemodel')

    def getOverrides(self):
        return {(NS_SILVA_URI, 'content'): PageModelVersionHandler}

    def startElementNS(self, name, qname, attrs):
        if name == (NS_URI, 'pagemodel'):
            uid = self.generateOrReplaceId(attrs[(None, 'id')].encode('utf-8'))
            factory = self.parent().manage_addProduct[
                'silva.core.contentlayout']
            factory.manage_addPageModel(uid, '', no_default_version=True)
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'pagemodel'):
            self.notifyImport()


class PageModelVersionHandler(xmlimport.SilvaBaseHandler):

    def getOverrides(self):
        return {(NS_URI, 'design'): DesignHandler}

    def startElementNS(self, name, qname, attrs):
        if (NS_SILVA_URI, 'content') == name:
            uid = attrs[(None, 'version_id')].encode('utf-8')
            factory = self.parent().manage_addProduct[
                'silva.core.contentlayout']
            factory.manage_addPageModelVersion(uid, '')
            self.setResultId(uid)

    def endElementNS(self, name, qname):
        if (NS_SILVA_URI, 'content') == name:
            xmlimport.updateVersionCount(self)
            self.storeMetadata()
            self.storeWorkflow()

