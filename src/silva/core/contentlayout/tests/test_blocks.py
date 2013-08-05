# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject
from zope.component import getUtility

from Acquisition import aq_chain
from Products.Silva.testing import TestRequest, TestCase

from silva.core.interfaces import IImage
from silva.core.references.interfaces import IReferenceService
from silva.core.references.reference import get_content_id
from zeam.component import getWrapper

from .. import Block
from ..blocks.contents import ReferenceBlock
from ..blocks.text import TextBlock
from ..blocks.slot import BlockSlot
from ..blocks.registry import get_block_configuration
from ..interfaces import IBlock, ISlot, IBlockController, IBlockSlot
from ..interfaces import IBlockConfiguration, IBlockConfigurations
from ..testing import FunctionalLayer


class MockView(object):

    def __init__(self, context):
        assert context is not None, u'Invalid context'
        self.request = TestRequest()
        self.context = context
        self.root_url = 'http://localhost'


class BlockTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')

    def test_block(self):
        """Verify default block.
        """
        block = Block()
        self.assertTrue(verifyObject(IBlock, block))

    def test_configuration(self):
        """Verify default block configuration.
        """
        context = self.root.page.get_editable()
        configurations = get_block_configuration(Block, context)
        self.assertTrue(verifyObject(IBlockConfigurations, configurations))
        self.assertEqual(len(configurations.get_all()), 1)

        configuration = configurations.get_by_identifier()
        self.assertTrue(verifyObject(IBlockConfiguration, configuration))
        self.assertEqual(configuration.block, Block)


class ReferenceBlockTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('test', 'Test')
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')

    def test_block(self):
        """Verify reference block.
        """
        block = ReferenceBlock()
        self.assertTrue(verifyObject(IBlock, block))

    def test_configuration(self):
        """Verify reference block configuration.
        """
        context = self.root.page.get_editable()
        view = MockView(context)

        configurations = get_block_configuration(ReferenceBlock, context)
        self.assertTrue(verifyObject(IBlockConfigurations, configurations))
        self.assertEqual(len(configurations.get_all()), 1)

        configuration = configurations.get_by_identifier()
        self.assertTrue(verifyObject(IBlockConfiguration, configuration))
        self.assertEqual(
            configuration.identifier,
            'site-content')
        self.assertEqual(
            configuration.title,
            'Site content')
        self.assertEqual(
            configuration.block,
            ReferenceBlock)
        self.assertEqual(
            configuration.get_icon(view),
            'http://localhost/++resource++icon-blocks-site-content.png')
        self.assertTrue(configuration.is_available(view))

    def test_controller(self):
        """Verify reference block controller.
        """
        service = getUtility(IReferenceService)
        context = self.root.page.get_editable()
        view = MockView(context)
        block = ReferenceBlock()
        # By default the page has no reference
        self.assertEqual(
            list(service.get_references_from(context)),
            [])

        # Test controller
        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))
        self.assertEqual(controller.editable(), True)
        self.assertEqual(controller.content, None)
        self.assertMultiLineEqual(
            controller.render(view),
            'Content reference is broken or missing.')
        self.assertEqual(
            controller.indexes(),
            [])
        self.assertEqual(
            controller.fulltext(),
            [])

        # Change the reference.
        controller.content = self.root.test
        self.assertEqual(controller.content, self.root.test)
        self.assertMultiLineEqual(
            controller.render(view),
            'Content is not viewable.')
        self.assertEqual(
            controller.indexes(),
            [])
        self.assertEqual(
            controller.fulltext(),
            [])
        self.assertEqual(
            len(list(service.get_references_from(context))),
            1)

        # Remove the reference.
        controller.remove()
        self.assertEqual(controller.content, None)
        self.assertEqual(
            list(service.get_references_from(context)),
            [])


class TextBlockTestCase(TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('test', 'Test')
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')

    def test_block(self):
        """Verify reference block.
        """
        block = TextBlock()
        self.assertTrue(verifyObject(IBlock, block))

    def test_configuration(self):
        """Verify reference block configuration.
        """
        context = self.root.page.get_editable()
        view = MockView(context)

        configurations = get_block_configuration(TextBlock, context)
        self.assertTrue(verifyObject(IBlockConfigurations, configurations))
        self.assertEqual(len(configurations.get_all()), 1)

        configuration = configurations.get_by_identifier()
        self.assertTrue(verifyObject(IBlockConfiguration, configuration))
        self.assertEqual(
            configuration.identifier,
            'text')
        self.assertEqual(
            configuration.title,
            'Text')
        self.assertEqual(
            configuration.block,
            TextBlock)
        self.assertEqual(
            configuration.get_icon(view),
            'http://localhost/++resource++icon-blocks-text.png')
        self.assertTrue(configuration.is_available(view))

    def test_controller_empty(self):
        """Verify reference block controller, with an empty text.
        """
        context = self.root.page.get_editable()
        view = MockView(context)
        block = TextBlock()
        service = getUtility(IReferenceService)
        # By default the page has no reference
        self.assertEqual(list(service.get_references_from(context)), [])

        # Test controller
        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))
        self.assertEqual(controller.editable(), True)
        self.assertXMLEqual(controller.text, '')
        self.assertXMLEqual(
            controller.render(view),
            '')
        self.assertEqual(
            controller.indexes(),
            [])
        self.assertEqual(
            controller.fulltext(),
            [])
        self.assertEqual(
            list(service.get_references_from(context)),
            [])

        # Remove the block.
        controller.remove()
        self.assertXMLEqual(
            controller.text,
            u'')
        self.assertEqual(
            list(service.get_references_from(context)),
            [])

    def test_controller_text(self):
        """Verify text controller with a simple piece of text.
        """
        context = self.root.page.get_editable()
        view = MockView(context)
        block = TextBlock()
        service = getUtility(IReferenceService)
        # By default the page has no reference
        self.assertEqual(list(service.get_references_from(context)), [])

        # Test controller
        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))
        self.assertEqual(controller.editable(), True)

        # Change the text.
        TEXT = """
<p>
   This is some rich text.
</p>"""
        controller.text = TEXT
        self.assertXMLEqual(controller.text, TEXT)
        self.assertXMLEqual(
            controller.render(view),
            TEXT)
        self.assertEqual(
            controller.indexes(),
            [])
        self.assertEqual(
            controller.fulltext(),
            ['This is some rich text.'])
        self.assertEqual(
            list(service.get_references_from(context)),
            [])

        # Remove the block.
        controller.remove()
        self.assertXMLEqual(
            controller.text,
            u'')
        self.assertEqual(
            list(service.get_references_from(context)),
            [])

    def test_controller_link(self):
        """Verify text block controller with a piece of text that
        contains a link.
        """
        context = self.root.page.get_editable()
        view = MockView(context)
        block = TextBlock()
        service = getUtility(IReferenceService)
        # By default the page has no reference
        self.assertEqual(list(service.get_references_from(context)), [])

        # Test controller
        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))
        self.assertEqual(controller.editable(), True)

        # Change the text with a reference.
        TEXT_LINK = u"""
<p>
   <a class="link"
      href="javascript:void(0)"
      data-silva-reference="new"
      data-silva-target="%s">Test élaboré</a>
</p>
""" % (get_content_id(self.root.test))
        controller.text = TEXT_LINK

        # A reference have been created to encode the link.
        references = list(service.get_references_from(context))
        self.assertEqual(len(references), 1)
        reference = references[0]
        self.assertEqual(reference.source, context)
        self.assertEqual(aq_chain(reference.source), aq_chain(context))
        self.assertEqual(reference.target, self.root.test)
        self.assertEqual(aq_chain(reference.target), aq_chain(self.root.test))
        self.assertEqual(len(reference.tags), 2)
        reference_target = reference.target_id
        reference_name = reference.tags[1]
        self.assertEqual(
            reference.tags,
            [u'%s link' % block.identifier, reference_name])

        self.assertXMLEqual(
            controller.text,
            u"""
<p>
   <a class="link" data-silva-reference="%s" data-silva-target="%s" href="javascript:void(0)">Test &#233;labor&#233;</a>
</p>""" % (reference_name, reference_target))
        self.assertXMLEqual(
            controller.render(view),
            u"""
<p>
   <a class="link" href="http://localhost/root/test">Test &#233;labor&#233;</a>
</p>""")
        self.assertEqual(
            controller.indexes(),
            [])
        self.assertEqual(
            controller.fulltext(),
            [u'Test élaboré'])

        # Remove the text. This should clean the reference.
        controller.remove()
        self.assertXMLEqual(
            controller.text,
            u'')
        self.assertEqual(
            list(service.get_references_from(context)),
            [])

    def test_controller_anchor(self):
        """Verify text block controller with a piece of text that
        contains some anchors.
        """
        context = self.root.page.get_editable()
        view = MockView(context)
        block = TextBlock()

        # Test controller
        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))
        self.assertEqual(controller.editable(), True)

        # Change the text with a reference.
        TEXT_ANCHOR = """
<p>
   <a class="anchor" name="simple" title="Simple Anchor">Simple Anchor</a>
   The ultimate store of the anchors.

   <a class="anchor" name="advanced" title="Advanced Anchor">Advanced Anchor</a>

</p>
"""

        TEXT_ANCHOR_STORED = """
<p>
   <a class="anchor" name="simple" title="Simple Anchor">Simple Anchor</a>
   The ultimate store of the anchors.

   <a class="anchor" name="advanced" title="Advanced Anchor">Advanced Anchor</a>

</p>
"""

        controller.text = TEXT_ANCHOR
        self.assertXMLEqual(
            controller.text,
            TEXT_ANCHOR_STORED)
        self.assertXMLEqual(
            controller.render(view),
            TEXT_ANCHOR)
        indexes = controller.indexes()
        self.assertEqual(len(indexes), 2)

        # Remove the text. This should clean the reference.
        controller.remove()
        self.assertXMLEqual(
            controller.text,
            u'')
        self.assertEqual(
            controller.indexes(),
            [])


class BlockSlotTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()
        factory.manage_addMockupPage('page', 'Page')
        factory.manage_addPageModel('model', 'Model')

    def test_block(self):
        """Verify slot block, that is a block, and a slot.
        """
        block = BlockSlot()
        self.assertTrue(verifyObject(IBlock, block))
        self.assertTrue(verifyObject(ISlot, block))
        self.assertTrue(verifyObject(IBlockSlot, block))

        # By default the tag is section here.
        self.assertEqual(block.tag, 'section')
        self.assertEqual(block.css_class, '')

    def test_configuration(self):
        """Verify slot block configuration.
        """
        context = self.root.page.get_editable()
        view = MockView(context)

        configurations = get_block_configuration(BlockSlot, context)
        self.assertTrue(verifyObject(IBlockConfigurations, configurations))
        self.assertEqual(len(configurations.get_all()), 1)

        configuration = configurations.get_by_identifier()
        self.assertTrue(verifyObject(IBlockConfiguration, configuration))
        self.assertEqual(
            configuration.identifier,
            'slot')
        self.assertEqual(
            configuration.title,
            'Slot')
        self.assertEqual(
            configuration.block,
            BlockSlot)
        self.assertEqual(
            configuration.get_icon(view),
            'http://localhost/++resource++icon-blocks-slot.png')

        # This block is only available on models.
        self.assertFalse(configuration.is_available(view))

        view = MockView(self.root.model.get_editable())
        self.assertTrue(configuration.is_available(view))

    def test_controller(self):
        """Test block slot controller.
        """
        view = MockView(self.root.page.get_editable())
        block = BlockSlot()

        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))

        self.assertEqual(controller.get_tag(), 'section')
        self.assertEqual(controller.get_css_class(), '')
        controller.set_identifier('modified-identifier')
        self.assertEqual(controller.get_identifier(), 'modified-identifier')

        # Check cs_blacklist and cs_whitelist
        self.assertEqual(controller.get_cs_blacklist(), set())
        self.assertEqual(controller.get_cs_whitelist(), set())

        # Check content_restriction
        self.assertIs(controller.get_content_restriction(), None)
        self.assertIs(controller.get_content_restriction_name(), None)

        controller.set_content_restriction(IImage)
        self.assertIs(controller.get_content_restriction(), IImage)
        self.assertEqual(
            controller.get_content_restriction_name(),
            'Silva Image')

        controller.set_content_restriction(None)
        self.assertIs(controller.get_content_restriction(), None)
        self.assertIs(controller.get_content_restriction_name(), None)

        # Check block_all
        self.assertFalse(controller.get_block_all())

        controller.set_block_all(True)
        self.assertTrue(controller.get_block_all())

        controller.set_block_all(False)
        self.assertFalse(controller.get_block_all())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BlockTestCase))
    suite.addTest(unittest.makeSuite(ReferenceBlockTestCase))
    suite.addTest(unittest.makeSuite(TextBlockTestCase))
    suite.addTest(unittest.makeSuite(BlockSlotTestCase))
    return suite
