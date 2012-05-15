
import unittest

from Products.Silva.ExtensionRegistry import extensionRegistry
from zope.interface.verify import verifyObject, verifyClass

from .. import restrictions, Slot, Block
from ..interfaces import ISlot, IDesign, IDesignLookup
from ..designs.registry import registry as design_registry
from ..testing import FunctionalLayer


class DesignTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockPage('page', 'Page')

    def test_registry(self):
        """Test the different lookup methods on the registry.
        """
        self.assertTrue(verifyObject(IDesignLookup, design_registry))
        demo_designs = design_registry.lookup_design(self.root.page)
        demo_designs_by_id = {}

        self.assertEqual(len(demo_designs), 3)
        for design in demo_designs:
            self.assertTrue(verifyClass(IDesign, design))
            demo_designs_by_id[design.get_identifier()] = design
        self.assertEqual(len(demo_designs_by_id), 3)

        # Test lookup_design_by_name
        self.assertIn('demo.one_column', demo_designs_by_id)
        self.assertIs(
            design_registry.lookup_design_by_name('demo.one_column'),
            demo_designs_by_id['demo.one_column'])

        # Test lookup_design_by_addable
        self.assertItemsEqual(
            design_registry.lookup_design_by_addable(
                self.root,
                extensionRegistry.get_addable('Mock Page')),
            demo_designs)

    def test_slot(self):
        """Test slot definition.
        """
        slot = Slot()
        content_restriction = restrictions.Content()
        all_restriction = restrictions.BlockAll()
        slot_with_restriction = Slot(
            tag='nav',
            css_class='navigation',
            restrictions=[content_restriction, all_restriction])
        self.assertTrue(verifyObject(ISlot, slot))
        self.assertEqual(slot.tag, 'div')
        self.assertEqual(slot.css_class, None)
        self.assertEqual(slot.get_existing_restriction(Block()), None)
        self.assertTrue(verifyObject(ISlot, slot_with_restriction))
        self.assertEqual(slot_with_restriction.tag, 'nav')
        self.assertEqual(slot_with_restriction.css_class, 'navigation')
        self.assertEqual(
            slot_with_restriction.get_existing_restriction(Block()),
            all_restriction)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DesignTestCase))
    return suite
