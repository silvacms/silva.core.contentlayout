# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject
from zope.component import getUtility

from silva.core.references.interfaces import IReferenceService
from silva.core.interfaces.adapters import IPublicationWorkflow
from silva.core.interfaces.errors import ContentError

from ..interfaces import IPageModel, IPageModelVersion
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
        editable = model.get_editable()
        self.assertNotEqual(editable, None)
        self.assertTrue(verifyObject(IPageModelVersion, editable))

        identifier = editable.get_design_identifier()
        self.assertNotIn(identifier, (None, 'default'))
        self.assertEqual(editable.get_all_design_identifiers(),
                         [identifier, 'default'])


class ModelReferenceTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()
        factory.manage_addPageModel('model', 'Model')
        IPublicationWorkflow(self.root.model).publish()
        factory.manage_addMockupPage('page', None)
        version = self.root.page.get_editable()
        version.set_design(self.root.model.get_viewable())

        self.layer.login('manager')

    def test_create_reference_when_associate(self):
        """If a page use a model, a reference is created to it.
        """
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
        """If a page no longer use a model, the reference of this page
        to this model is deleted.
        """
        get_reference = getUtility(IReferenceService).get_reference
        version = self.root.page.get_editable()

        version.set_design(None)
        reference = get_reference(version, name=PAGE_TO_DESIGN_REF_NAME)
        self.assertIs(reference, None)

    def test_used_model_cannot_be_deleted(self):
        """A model that is used by a page cannot be deleted.
        """
        IPublicationWorkflow(self.root.model).close()

        with self.assertRaises(BrokenReferenceError):
            self.root.manage_delObjects('model')

    def test_page_and_model_are_deleted(self):
        """If a page is using a model and the page is deleted,
        references to this model are cleaned, and the model can be deleted.
        """
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

    def test_page_use_model_latest_version(self):
        """If you make a new version of the model, and it gets
        published, it get used by existing pages.
        """
        version = self.root.page.get_editable()
        self.assertEquals(self.root.model.get_viewable(), version.get_design())

        # We make a copy, the publish version is still used.
        IPublicationWorkflow(self.root.model).new_version()
        editable = self.root.model.get_editable()
        self.assertNotEquals(editable, version.get_design())

        # The version is published, the new one is used.
        IPublicationWorkflow(self.root.model).publish()
        self.assertEquals(editable, version.get_design())

    def test_model_cannot_use_itself(self):
        """You cannot select as model the same model itself or an
        another model who is using it.
        """
        IPublicationWorkflow(self.root.model).new_version()
        editable = self.root.model.get_editable()
        with self.assertRaises(ContentError):
            editable.set_design(self.root.model.get_viewable())

        # Set an self.root.other to use self.root.model
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('other', 'Other Model')
        self.root.other.get_editable().set_design(editable)
        IPublicationWorkflow(self.root.other).publish()

        # This will still make a loop.
        with self.assertRaises(ContentError):
            editable.set_design(self.root.other.get_viewable())

    def test_regression_model_using_itself_does_not_loop(self):
        """If a model uses itself, you can still use its API without
        infinite loop. This uses to happen, making impossible to fix
        the model.
        """
        IPublicationWorkflow(self.root.model).new_version()
        editable = self.root.model.get_editable()
        # We do it by hand as this is no longer possible with set_design
        editable._design_name = editable.get_design_identifier()
        IPublicationWorkflow(self.root.model).publish()

        viewable = self.root.model.get_viewable()
        identifier = viewable.get_design_identifier()
        self.assertNotIn(identifier, (None, 'default'))
        self.assertEqual(viewable.get_all_design_identifiers(), [identifier])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelsTestCase))
    suite.addTest(unittest.makeSuite(ModelReferenceTestCase))
    return suite
