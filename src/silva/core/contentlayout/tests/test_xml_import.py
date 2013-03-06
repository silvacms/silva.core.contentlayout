# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.component import getUtility

from Products.Silva.testing import TestRequest
from Products.Silva.tests.test_xml_import import SilvaXMLTestCase

from silva.core.interfaces.content import IImage, ILink
from silva.core.references.reference import ReferenceSet
from silva.core.references.interfaces import IReferenceService
from zeam.component import getWrapper

from ..blocks.contents import ReferenceBlock
from ..blocks.slot import BlockSlot
from ..blocks.source import SourceBlock
from ..blocks.text import TextBlock
from ..interfaces import IBlockManager, IBlockController
from ..model import PageModel, PageModelVersion
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
            'test_import_pagemodel.silvaxml',
            ['/root/folder',
             '/root/model',
             '/root/image'])
        self.assertEqual(
            importer.getProblems(),
            [('Missing image file in the import: assets/1.', self.root.image)])

        page_model = self.root._getOb('model')
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
        self.assertEquals(3, len(slot1))
        slot2 = manager.get_slot('two')
        _, slot_block = slot2[0]
        self.assertIsInstance(slot_block, BlockSlot)
        # restrictions
        restrictions = slot_block._restrictions
        self.assertEquals([restrict.CodeSourceName,
                           restrict.Content,
                           restrict.BlockAll],
                          [r.__class__ for r in restrictions])
        self.assertEquals(set(['allow1', 'allow2']),
                          restrictions[0].allowed)
        self.assertEquals(set(['dis1', 'dis2']),
                          restrictions[0].disallowed)
        self.assertEquals(IImage, restrictions[1].schema)

        # text block
        self.assertEquals(3, len(slot2))
        _, text_block = slot2[1]
        self.assertIsInstance(text_block, TextBlock)
        controller = getWrapper(
            (text_block, version, TestRequest()),
            IBlockController)
        self.assertXMLEqual("<div>text</div>", controller.text)

        _, ref_block = slot1[1]
        self.assertIsInstance(ref_block, ReferenceBlock)
        controller = getWrapper(
            (ref_block, version, TestRequest()),
            IBlockController)
        self.assertEquals(controller.content, self.root.image)

        _, source_block = slot1[2]
        self.assertIsInstance(source_block, SourceBlock)
        controller = getWrapper(
            (source_block, version, TestRequest()),
            IBlockController)
        params, _ = controller.manager.get_parameters(source_block.identifier)
        self.assertEquals('A joke is a very serious thing.', params.citation)
        self.assertEquals('Winston Churchill', params.author)

        _, source_block_with_ref = slot2[2]
        self.assertIsInstance(source_block_with_ref, SourceBlock)
        controller = getWrapper(
            (source_block_with_ref, version, TestRequest()),
            IBlockController)
        params, _ = controller.manager.get_parameters(
            source_block_with_ref.identifier)
        self.assertIn(self.root.folder,  ReferenceSet(version, params.paths))
        self.assertEquals(set(['Silva Publication', 'Silva Folder']),
                          set(params.toc_types))

    def test_import_text_block_with_refs(self):
        importer = self.assertImportFile(
            'test_import_text_block_with_refs.silvaxml',
            ['/root/model',
             '/root/link'])
        self.assertEqual(importer.getProblems(), [])

        model = self.root.model.get_editable()
        self.assertIsInstance(model, PageModelVersion)
        manager = IBlockManager(model)
        slot1 = manager.get_slot('one')
        self.assertEquals(1, len(slot1))
        _, text_block = slot1[0]
        self.assertIsInstance(text_block, TextBlock)
        ref_service = getUtility(IReferenceService)
        references = list(ref_service.get_references_from(model))
        self.assertEquals(1, len(references))
        reference = references[0]
        link = reference.target
        self.assertTrue(ILink.providedBy(link))
        self.assertEquals(2, len(reference.tags))
        reference_type = reference.tags[0]
        reference_name = reference.tags[1]
        self.assertEquals("%s link" % text_block.identifier, reference_type)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PageModelImportTestCase))
    return suite
