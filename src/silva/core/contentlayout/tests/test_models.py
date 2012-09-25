# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject
from zope.component import getUtility

from silva.core.references.interfaces import IReferenceService
from silva.core.interfaces.adapters import IPublicationWorkflow

from ..interfaces import IPageModel
from ..testing import FunctionalLayer
from silva.core.contentlayout.model import PAGE_TO_DESIGN_REF_NAME
from silva.core.references.reference import BrokenReferenceError


class ModelsTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()

    def test_model(self):
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('model', 'Model')

        model = self.root._getOb('model', None)
        self.assertNotEqual(model, None)
        self.assertTrue(verifyObject(IPageModel, model))

    def test_service_list_page_model(self):
        # XXX to implement
        pass


class ModelReferenceTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('model', 'Model')
        IPublicationWorkflow(self.root.model).publish()
        factory.manage_addMockupPage('page', None)
        version = self.root.page.get_editable()
        version.set_design(self.root.model.get_viewable())

        self.layer.login('manager')


    def test_create_reference_when_associate(self):
        get_reference = getUtility(IReferenceService).get_reference
        version = self.root.page.get_editable()
        reference = get_reference(version, name=PAGE_TO_DESIGN_REF_NAME)
        self.assertIsNot(reference, None)
        self.assertEquals(reference.target, self.root.model)

        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('other', 'Other Model')
        IPublicationWorkflow(self.root.other).publish()
        version.set_design(self.root.other.get_viewable())

        reference = get_reference(version, name=PAGE_TO_DESIGN_REF_NAME)
        self.assertIsNot(reference, None)
        self.assertEquals(reference.target, self.root.other)

    def test_delete_reference_when_deassociate(self):
        get_reference = getUtility(IReferenceService).get_reference
        version = self.root.page.get_editable()

        version.set_design(None)
        reference = get_reference(version, name=PAGE_TO_DESIGN_REF_NAME)
        self.assertIs(reference, None)

    def test_page_model_removal_raise(self):
        IPublicationWorkflow(self.root.model).close()

        with self.assertRaises(BrokenReferenceError):
            self.root.manage_delObjects('model')

    def test_page_is_removed(self):
        version = self.root.page.get_editable()
        get_references_to = getUtility(IReferenceService).get_references_to
        references = list(get_references_to(
                self.root.model, name=PAGE_TO_DESIGN_REF_NAME))
        self.assertEquals(len(references), 1)
        self.assertEquals(version, references[0].source)
        self.root.manage_delObjects('page')

        references = list(get_references_to(
                self.root.model, name=PAGE_TO_DESIGN_REF_NAME))
        self.assertEquals(len(references), 0)
        self.root.manage_delObjects('model')

    def test_page_model_not_cached(self):
        version = self.root.page.get_editable()
        self.assertEquals(self.root.model.get_viewable(), version.get_design())
        IPublicationWorkflow(self.root.model).new_version()
        editable = self.root.model.get_editable()
        self.assertNotEquals(editable, version.get_design())
        IPublicationWorkflow(self.root.model).publish()
        self.assertEquals(editable, version.get_design())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelsTestCase))
    suite.addTest(unittest.makeSuite(ModelReferenceTestCase))
    return suite
