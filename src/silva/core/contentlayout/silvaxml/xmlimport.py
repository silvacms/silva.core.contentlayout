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


from . import NS_URI


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


# XXX: class SourceBlockHandler

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

            self.add_block(BlockSlot(**options))


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
            self._design = registry.lookup_design_by_name(attrs[(None, 'id')])

    def endElementNS(self, name, qname):
        if name == (NS_URI, 'design'):
            self.parent().set_design(self._design)
            del self._design


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

