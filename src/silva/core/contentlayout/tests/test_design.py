# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from Products.Silva.ExtensionRegistry import extensionRegistry
from zope.interface.verify import verifyObject, verifyClass

from ..designs.registry import registry as design_registry
from ..interfaces import IDesign, IDesignLookup
from ..testing import FunctionalLayer


class DesignTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')

    def test_registry(self):
        """Test the different lookup methods on the registry.
        """
        self.assertTrue(verifyObject(IDesignLookup, design_registry))
        demo_designs = design_registry.lookup_design(self.root.page)
        demo_designs_by_id = {}

        self.assertEqual(len(demo_designs), 4)
        for design in demo_designs:
            self.assertTrue(verifyClass(IDesign, design))
            demo_designs_by_id[design.get_identifier()] = design
        self.assertEqual(len(demo_designs_by_id), 4)

        # Test lookup_design_by_name
        self.assertIn('demo.one_column', demo_designs_by_id)
        self.assertIs(
            design_registry.lookup_design_by_name('demo.one_column'),
            demo_designs_by_id['demo.one_column'])

        # Test lookup_design_by_addable
        self.assertItemsEqual(
            design_registry.lookup_design_by_addable(
                self.root,
                extensionRegistry.get_addable('Mockup Page')),
            demo_designs)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DesignTestCase))
    return suite
