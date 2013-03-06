# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.component import queryUtility
from zope.interface.verify import verifyObject

from ..interfaces import IContentLayoutService
from ..testing import FunctionalLayer


class ServiceTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_service(self):
        # Service is not installed by default
        service = queryUtility(IContentLayoutService)
        self.assertEqual(service, None)

        # Add one
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addContentLayoutService()

        service = queryUtility(IContentLayoutService)
        self.assertNotEqual(service, None)
        self.assertTrue(verifyObject(IContentLayoutService, service))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ServiceTestCase))
    return suite

