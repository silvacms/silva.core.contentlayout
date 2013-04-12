# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.component import getUtility
from zope.interface.verify import verifyObject

from Products.Silva.testing import TestRequest
from Products.Silva.tests.test_xml_import import SilvaXMLTestCase

from silva.core.interfaces.content import IImage, ILink
from silva.core.references.reference import ReferenceSet
from silva.core.references.interfaces import IReferenceService
from zeam.component import getWrapper

from ..blocks.contents import ReferenceBlock
from ..blocks.source import SourceBlock
from ..blocks.text import TextBlock
from ..interfaces import IBlockManager, IBlockController, IBlockSlot
from ..interfaces import IPageModel, IPageModelVersion
from ..slots import restrictions as restrict
from ..testing import FunctionalLayer


class PageModelImportTestCase(SilvaXMLTestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('editor')
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()

    def test_import_page_model(self):
        importer = self.assertImportFile(
            'test_import_page_model.silvaxml',
            ['/root/folder',
             '/root/model',
             '/root/image'])
        self.assertEqual(
            importer.getProblems(),
            [('Missing image file in the import: assets/1.', self.root.image)])

        page_model = self.root._getOb('model')
        self.assertTrue(verifyObject(IPageModel, page_model))
        version = page_model.get_editable()
        self.assertTrue(verifyObject(IPageModelVersion, version))

        design = version.get_design()
        self.assertEqual(design.get_design_identifier(), 'adesign')

        manager = IBlockManager(version)
        self.assertTrue(verifyObject(IBlockManager, manager))
        self.assertItemsEqual(manager.get_slot_ids(), ['one', 'two'])

        slot1 = manager.get_slot('one')
        self.assertEqual(len(slot1), 3)
        slot2 = manager.get_slot('two')
        self.assertEqual(len(slot2), 3)

        # Slot block
        _, slot_block = slot2[0]
        self.assertTrue(verifyObject(IBlockSlot, slot_block))
        controller = getWrapper(
            (slot_block, version, TestRequest()),
            IBlockController)
        self.assertEqual(controller.get_tag(), 'div')
        self.assertEqual(controller.get_css_class(), 'large-area')
        self.assertEqual(controller.get_identifier(), 'content-area')
        self.assertEqual(
            controller.get_cs_blacklist(),
            set(['dis1', 'dis2']))
        self.assertEqual(
            controller.get_cs_whitelist(),
            set(['allow1', 'allow2']))
        self.assertEqual(
            controller.get_content_restriction_name(),
            'Silva Image')
        self.assertEqual(controller.get_block_all(), True)

        # Text block
        _, text_block = slot2[1]
        self.assertIsInstance(text_block, TextBlock)
        controller = getWrapper(
            (text_block, version, TestRequest()),
            IBlockController)
        self.assertXMLEqual(controller.text, "<div>text</div>")

        # Reference block
        _, ref_block = slot1[1]
        self.assertIsInstance(ref_block, ReferenceBlock)
        controller = getWrapper(
            (ref_block, version, TestRequest()),
            IBlockController)
        self.assertEqual(controller.content, self.root.image)

        # Source block
        _, source_block = slot1[2]
        self.assertIsInstance(source_block, SourceBlock)
        controller = getWrapper(
            (source_block, version, TestRequest()),
            IBlockController)
        params = controller.getContent()
        self.assertEqual(params.citation, 'A joke is a very serious thing.')
        self.assertEqual(params.author, 'Winston Churchill')

        _, source_block_with_ref = slot2[2]
        self.assertIsInstance(source_block_with_ref, SourceBlock)
        controller = getWrapper(
            (source_block_with_ref, version, TestRequest()),
            IBlockController)
        params = controller.getContent()
        self.assertIn(self.root.folder, ReferenceSet(version, params.paths))
        self.assertEqual(
            set(params.toc_types),
            set(['Silva Publication', 'Silva Folder']))

    def test_import_text_block_with_references(self):
        importer = self.assertImportFile(
            'test_import_text_block_with_references.silvaxml',
            ['/root/model',
             '/root/link'])
        self.assertEqual(importer.getProblems(), [])

        model = self.root._getOb('model')
        self.assertTrue(verifyObject(IPageModel, model))
        version = model.get_editable()
        self.assertTrue(verifyObject(IPageModelVersion, version))

        manager = IBlockManager(version)
        slot1 = manager.get_slot('one')
        self.assertEqual(1, len(slot1))
        _, text_block = slot1[0]
        self.assertIsInstance(text_block, TextBlock)
        references = list(
            getUtility(IReferenceService).get_references_from(version))
        self.assertEqual(1, len(references))
        reference = references[0]
        link = reference.target
        self.assertTrue(ILink.providedBy(link))
        self.assertEqual(2, len(reference.tags))
        reference_type = reference.tags[0]
        self.assertEqual("%s link" % text_block.identifier, reference_type)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PageModelImportTestCase))
    return suite
