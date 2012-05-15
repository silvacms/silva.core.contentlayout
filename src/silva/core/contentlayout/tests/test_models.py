

import unittest

from silva.core.contentlayout.testing import FunctionalLayer


class ModelsTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()




def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ModelsTestCase))
    return suite
