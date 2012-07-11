
import unittest

from zope.interface.verify import verifyObject
from zeam.component import getWrapper

from Products.Silva.testing import TestRequest

from .. import Block
from ..blocks.contents import ReferenceBlock
from ..blocks.registry import get_block_configuration
from ..interfaces import IBlock, IBlockController
from ..interfaces import IBlockConfiguration, IBlockConfigurations
from ..testing import FunctionalLayer


class MockView(object):

    def __init__(self, context=None):
        self.request = TestRequest()
        self.context = context
        self.root_url = 'http://localhost'


class BlocksTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        factory.manage_addMockupVersionedContent('test', 'Test')
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')

    def test_default_block(self):
        """Verify default block.
        """
        block = Block()
        self.assertTrue(verifyObject(IBlock, block))

    def test_default_block_configuration(self):
        """Verify default block configuration.
        """
        context = self.root.page.get_editable()
        configurations = get_block_configuration(Block, context)
        self.assertTrue(verifyObject(IBlockConfigurations, configurations))
        self.assertEqual(len(configurations.get_all()), 1)

        configuration = configurations.get_by_identifier()
        self.assertTrue(verifyObject(IBlockConfiguration, configuration))
        self.assertEqual(configuration.block, Block)

    def test_reference_block(self):
        """Verify reference block.
        """
        block = ReferenceBlock()
        self.assertTrue(verifyObject(IBlock, block))

    def test_reference_block_configuration(self):
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

    def test_reference_block_controller(self):
        """Verify reference block controller.
        """
        context = self.root.page.get_viewable()
        view = MockView(context)
        block = ReferenceBlock()

        # Test controller
        controller = getWrapper(
            (block, view.context, view.request),
            IBlockController,
            default=None)
        self.assertTrue(verifyObject(IBlockController, controller))
        self.assertEqual(controller.editable(), True)
        self.assertEqual(controller.content, None)
        self.assertEqual(
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
        self.assertEqual(
            controller.render(view),
            'Content is not viewable.')
        self.assertEqual(
            controller.indexes(),
            [])
        self.assertEqual(
            controller.fulltext(),
            [])

        # Remove the reference.
        controller.remove()
        self.assertEqual(controller.content, None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BlocksTestCase))
    return suite
