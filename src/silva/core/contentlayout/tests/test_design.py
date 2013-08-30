# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from Products.Silva.testing import TestRequest
from Products.Silva.ExtensionRegistry import extensionRegistry
from zope.interface.verify import verifyObject, verifyClass
from zope.schema.interfaces import ISource
from zeam.form.base import FormData

from ..designs.registry import registry as design_registry
from ..interfaces import IDesign, IDesignLookup
from ..interfaces import design_identifier_source, design_source
from ..testing import FunctionalLayer


class DesignTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')

    def test_design_identifier_source(self):
        """Test the vocabulary used to list design identifiers (used
        in the service).
        """
        vocabulary = design_identifier_source(self.root)
        self.assertTrue(verifyObject(ISource, vocabulary))
        self.assertEqual(len(vocabulary), 4)
        self.assertItemsEqual(
            map(lambda v: v.token, vocabulary),
            ['adesign',
             'demo.advanced_template',
             'demo.one_column',
             'demo.two_column'])
        self.assertItemsEqual(
            map(lambda v: v.title, vocabulary),
            ['A Design for testing',
             u'Advanced design (StandardIssue)',
             u'One Column (standard)',
             u'Two Columns (standard)'])

    def test_design_source(self):
        """Test the vocabulary used to list design and page models in
        the form.
        """
        form = FormData(self.root.page.get_editable(), TestRequest())
        vocabulary = design_source(form)
        self.assertTrue(verifyObject(ISource, vocabulary))
        self.assertEqual(len(vocabulary), 4)
        self.assertItemsEqual(
            map(lambda v: v.token, vocabulary),
            ['adesign',
             'demo.advanced_template',
             'demo.one_column',
             'demo.two_column'])
        self.assertItemsEqual(
            map(lambda v: v.title, vocabulary),
            ['A Design for testing',
             u'Advanced design (StandardIssue)',
             u'One Column (standard)',
             u'Two Columns (standard)'])
        self.assertItemsEqual(
            map(lambda v: v.icon, vocabulary),
            ['http://localhost/root/++static++/silva.core.contentlayout/design.png',
             'http://localhost/root/++static++/silva.core.contentlayout/design.png',
             'http://localhost/root/++resource++icon-designs-demo.one_column.png',
             'http://localhost/root/++resource++icon-designs-demo.two_column.png'])

    def test_registry(self):
        """Test the different lookup methods on the registry.
        """
        self.assertTrue(verifyObject(IDesignLookup, design_registry))
        demo_designs = design_registry.lookup_design(self.root.page)
        demo_designs_by_id = {}

        self.assertEqual(len(demo_designs), 4)
        for design in demo_designs:
            self.assertTrue(verifyClass(IDesign, design))
            demo_designs_by_id[design.get_design_identifier()] = design
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
