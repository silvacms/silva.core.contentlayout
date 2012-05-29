
from Products.Silva.tests.helpers import open_test_file
from Products.Silva.silvaxml.xmlexport import exportToString
from Products.Silva.tests.test_xml_export import SilvaXMLTestCase
from zope.publisher.browser import TestRequest
from zope.component import getMultiAdapter

from ..testing import FunctionalLayer
from ..designs.registry import registry
from ..blocks.contents import ReferenceBlock
# from ..blocks.source import SourceBlock
from ..blocks.text import TextBlock
from ..blocks.slot import BlockSlot
from .. import interfaces
from silva.core.contentlayout.slots import restrictions
from silva.core.interfaces import IImage

class TestExportPage(SilvaXMLTestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('exportbase', 'Export base')
        self.base_folder = self.root.exportbase
        factory = self.base_folder.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockPage('apage', 'Page')
        self.page = self.base_folder.apage.get_editable()
        self.design = registry.lookup_design_by_name('adesign')
        self.page.set_design(self.design)

    def test_export_design(self):
        xml, _ = exportToString(self.base_folder)
        self.assertExportEqual(
                    xml, 'test_export_design.silvaxml', globs=globals())

    def test_export_design_and_ref_block(self):
        factory = self.base_folder.manage_addProduct['Silva']
        with open_test_file('image.png', globals()) as image_file:
            factory.manage_addImage('image', 'Image', image_file)
        image = self.base_folder.image

        block = ReferenceBlock()
        controller = getMultiAdapter((block, self.page, TestRequest()),
                                     interfaces.IBlockController)
        controller.content = image
        manager = interfaces.IBlockManager(self.page)
        manager.add('one', block)

        xml, _ = exportToString(self.base_folder)
        self.assertExportEqual(
            xml, 'test_export_ref_block.silvaxml', globs=globals())

    def test_export_codesource_block(self):
        self.assertFalse(True, 'Pending')

    def test_export_text_block(self):
        block = TextBlock()
        controller = getMultiAdapter((block, self.page, TestRequest()),
                                     interfaces.IBlockController)
        controller.text = "<div>text</div>"
        manager = interfaces.IBlockManager(self.page)
        manager.add('two', block)

        xml, _ = exportToString(self.base_folder)
        self.assertExportEqual(
            xml, 'test_export_text_block.silvaxml', globs=globals())

    def test_export_page_model(self):
        factory = self.base_folder.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('pm', 'A Page Model')
        page_model = self.base_folder.pm
        version = page_model.get_editable()
        version.set_design(self.design)

        text_block = TextBlock()
        controller = getMultiAdapter((text_block, self.page, TestRequest()),
                                     interfaces.IBlockController)
        controller.text = "<div>text</div>"

        manager = interfaces.IBlockManager(version)
        manager.add('two', text_block)
        manager.add('two', BlockSlot())
        manager.add('one', BlockSlot(restrictions=[
            restrictions.CodeSourceName(allowed=set(['allow1', 'allow2']),
                                        disallowed=set(['dis1', 'dis2'])),
            restrictions.Content(schema=IImage),
            restrictions.BlockAll()]))

        xml, _ = exportToString(self.base_folder)

        self.assertExportEqual(
            xml, 'test_export_page_model.silva.xml', globs=globals())
