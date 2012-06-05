
import unittest

from zope.interface.verify import verifyObject
from zope.component import getUtility

from silva.core.references.interfaces import IReferenceService
from silva.core.interfaces.adapters import IPublicationWorkflow

from ..interfaces import IPageModel
from ..testing import FunctionalLayer, FunctionalLayerWithService
from silva.core.contentlayout.model import PAGE_TO_DESIGN_REF_NAME
from silva.core.references.reference import BrokenReferenceError


class ModelsTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_model(self):
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel('model', 'Model')

        model = self.root._getOb('model', None)
        self.assertNotEqual(model, None)
        self.assertTrue(verifyObject(IPageModel, model))


class PageToModelReferenceTestCase(unittest.TestCase):
    layer = FunctionalLayerWithService

    def setUp(self):
        self.root = self.layer.get_application()
        self.layer.login('manager')
        self.reference_service = getUtility(IReferenceService)
        self.model = self._create_model('model')

    def _create_model(self, identifier):
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addPageModel(identifier, 'Model')
        model_content = self.root._getOb(identifier, None)
        assert model_content, 'model creation failed'
        IPublicationWorkflow(model_content).publish()
        return model_content.get_viewable()

    def _create_page_and_associate(self):
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockPage('apage', None)
        page = self.root._getOb('apage')
        version = page.get_editable()
        version.set_design(self.model)
        return version

    def test_create_reference_when_associate(self):
        version = self._create_page_and_associate()
        ref = self.reference_service.get_reference(version,
                                                   name=PAGE_TO_DESIGN_REF_NAME)
        self.assertTrue(ref)
        self.assertEquals(ref.target, self.model.get_silva_object())

        other_model = self._create_model('other')
        version.set_design(other_model)

        ref = self.reference_service.get_reference(version,
                                                   name=PAGE_TO_DESIGN_REF_NAME)
        self.assertTrue(ref)
        self.assertEquals(ref.target, other_model.get_silva_object())

    def test_delete_reference_when_deassociate(self):
        version = self._create_page_and_associate()
        version.set_design(None)
        ref = self.reference_service.get_reference(version,
                                                   name=PAGE_TO_DESIGN_REF_NAME)
        self.assertFalse(ref)

    def test_page_model_removal_raise(self):
        self._create_page_and_associate()
        IPublicationWorkflow(self.model.get_silva_object()).close()
        def remove():
            self.root.manage_delObjects('model')

        self.assertRaises(BrokenReferenceError, remove)

    def test_page_is_removed(self):
        version = self._create_page_and_associate()
        refs = list(self.reference_service.get_references_to(
            self.model.get_silva_object(), name=PAGE_TO_DESIGN_REF_NAME))
        self.assertEquals(version, refs[0].source)
        self.root.manage_delObjects('apage')
        refs = list(self.reference_service.get_references_to(
            self.model.get_silva_object(), name=PAGE_TO_DESIGN_REF_NAME))
        self.assertFalse(refs)
        self.root.manage_delObjects('model')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelsTestCase))
    suite.addTest(unittest.makeSuite(PageToModelReferenceTestCase))
    return suite
