

import unittest

from silva.core.contentlayout.interfaces import IPageModel
from silva.core.contentlayout.testing import FunctionalLayer
from zope.interface.verify import verifyObject


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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelsTestCase))
    return suite
