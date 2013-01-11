# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from Products.Silva.testing import TestRequest
from Products.Silva.tests.test_xml_export import SilvaXMLTestCase
from Products.SilvaExternalSources.interfaces import IExternalSourceManager

from zope.intid.interfaces import IIntIds
from zope.component import getUtility

from silva.core.contentlayout.blocks.source import SourceBlock
from silva.core.contentlayout.slots import restrictions
from silva.core.interfaces import IImage
from zeam.component import getWrapper
from zeam.form import silva as silvaforms

from .. import interfaces
from ..blocks.contents import ReferenceBlock
from ..blocks.slot import BlockSlot
from ..blocks.text import TextBlock
from ..designs.registry import registry
from ..testing import FunctionalLayer


class PageXMLExportTestCase(SilvaXMLTestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addFolder('exportbase', 'Export base')
        self.base_folder = self.root.exportbase
        factory = self.base_folder.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')
        self.page = self.base_folder.page.get_editable()
        self.design = registry.lookup_design_by_name('adesign')
        self.page.set_design(self.design)

    def test_export_design(self):
        exporter = self.assertExportEqual(
            self.root.exportbase,
            'test_export_design.silvaxml')
        self.assertEqual(exporter.getZexpPaths(), [])
        self.assertEqual(exporter.getAssetPaths(), [])
        self.assertEqual(exporter.getProblems(), [])

    def test_export_design_and_reference_block(self):
        factory = self.root.exportbase.manage_addProduct['Silva']
        with self.layer.open_fixture('image.png') as image_file:
            factory.manage_addImage('image', 'Image', image_file)

        block = ReferenceBlock()
        controller = getWrapper(
            (block, self.page, TestRequest()),
            interfaces.IBlockController)
        controller.content = self.root.exportbase.image
        manager = interfaces.IBlockManager(self.page)
        manager.add('one', block)

        exporter = self.assertExportEqual(
            self.root.exportbase,
            'test_export_ref_block.silvaxml')
        self.assertEqual(
            exporter.getZexpPaths(),
            [])
        self.assertEqual(
            exporter.getAssetPaths(),
            [(('', 'root', 'exportbase', 'image'), '1')])
        self.assertEqual(
            exporter.getProblems(),
            [])

    def test_export_text_block(self):
        block = TextBlock(identifier='text block 1')
        controller = getWrapper(
            (block, self.page, TestRequest()),
            interfaces.IBlockController)
        controller.text = "<div>text</div>"
        manager = interfaces.IBlockManager(self.page)
        manager.add('two', block)

        exporter = self.assertExportEqual(
            self.root.exportbase,
            'test_export_text_block.silvaxml')
        self.assertEqual(exporter.getZexpPaths(), [])
        self.assertEqual(exporter.getAssetPaths(), [])
        self.assertEqual(exporter.getProblems(), [])

    def test_export_source_block(self):
        source_manager = getWrapper(self.page, IExternalSourceManager)
        parameters = dict(field_citation="A joke is a very serious thing.",
                          field_author="Winston Churchill")
        request = TestRequest(form=parameters)
        controller = source_manager(request, name='cs_citation')
        marker = controller.create()
        self.assertIs(marker, silvaforms.SUCCESS)
        manager = interfaces.IBlockManager(self.page)
        manager.add('one', SourceBlock(controller.getId()))

        exporter = self.assertExportEqual(
            self.root.exportbase,
            'test_export_source_block.silvaxml')
        self.assertEqual(exporter.getZexpPaths(), [])
        self.assertEqual(exporter.getAssetPaths(), [])
        self.assertEqual(exporter.getProblems(), [])

    def test_export_source_block_with_reference(self):
        source_manager = getWrapper(self.page, IExternalSourceManager)
        intids = getUtility(IIntIds)
        folder_id = intids.register(self.base_folder)
        parameters = dict(field_paths=str(folder_id),
                          field_toc_types="Silva Folder",
                          field_depth="0",
                          field_sort_on="silva",
                          field_order="normal")
        request = TestRequest(form=parameters)
        controller = source_manager(request, name='cs_toc')
        marker = controller.create()
        self.assertIs(marker, silvaforms.SUCCESS)

        manager = interfaces.IBlockManager(self.page)
        manager.add('two', SourceBlock(controller.getId()))

        exporter = self.assertExportEqual(
            self.root.exportbase,
            'test_export_source_block_with_reference.silvaxml')
        self.assertEqual(exporter.getZexpPaths(), [])
        self.assertEqual(exporter.getAssetPaths(), [])
        self.assertEqual(exporter.getProblems(), [])

    def test_export_page_model(self):
        factory = self.root.exportbase.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('model', 'A Page Model')
        version = self.root.exportbase.model.get_editable()
        version.set_design(self.design)

        text_block = TextBlock(identifier='text block 1')
        controller = getWrapper(
            (text_block, self.page, TestRequest()),
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

        exporter = self.assertExportEqual(
            self.root.exportbase,
            'test_export_page_model.silvaxml')
        self.assertEqual(exporter.getZexpPaths(), [])
        self.assertEqual(exporter.getAssetPaths(), [])
        self.assertEqual(exporter.getProblems(), [])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PageXMLExportTestCase))
    return suite
