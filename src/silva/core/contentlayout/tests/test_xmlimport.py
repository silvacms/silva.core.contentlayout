
from zope.publisher.browser import TestRequest
from zope.component import getMultiAdapter, getUtility

from silva.core.messages.interfaces import IMessageService
from Products.Silva.tests.test_xml_import import SilvaXMLTestCase
from ..testing import FunctionalLayer
from ..model import PageModel, PageModelVersion
from ..interfaces import IBlockManager, IBlockController
from ..blocks.text import TextBlock
from ..blocks.contents import ReferenceBlock


class PageModelImportTest(SilvaXMLTestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('exportbase', 'Export base')
        self.base_folder = self.root.exportbase
        self.layer.login('editor')

    def test_import_page_model(self):
        self.import_file('test_import_pagemodel.silvaxml', globs=globals())

        message_service = getUtility(IMessageService)
        errors = message_service.receive(TestRequest(), namespace='error')
        self.assertEquals(0, len(errors),
            "import warning: " + "\n".join(map(str, errors)))

        page_model = self.root._getOb('pm')
        self.assertTrue(page_model is not None)
        version = page_model._getOb('0')
        self.assertIsInstance(page_model, PageModel)
        self.assertIsInstance(version, PageModelVersion)
        design = version.get_design()
        self.assertEquals('adesign', design.get_identifier())
        slots = version.slots
        self.assertEquals(2, len(slots))
        manager = IBlockManager(version)
        slot1 = manager.get_slot('one')
        self.assertEquals(2, len(slot1))
        slot2 = manager.get_slot('two')
        self.assertEquals(2, len(slot2))
        _, text_block = slot2[1]
        self.assertIsInstance(text_block, TextBlock)
        controller = getMultiAdapter((text_block, version, TestRequest()),
                                     IBlockController)
        self.assertXMLEqual("<div>text</div>", controller.text)

        _, ref_block = slot1[1]
        self.assertIsInstance(ref_block, ReferenceBlock)
        controller = getMultiAdapter((ref_block, version, TestRequest()),
                                     IBlockController)
        self.assertEquals(controller.content, self.root.image)

