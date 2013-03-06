# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject

from .. import restrictions
from ..interfaces import ISlotRestriction, IContentSlotRestriction
from ..testing import FunctionalLayer


class RestrictionsTestCase(unittest.TestCase):
    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()

    def test_implementation(self):
        self.assertTrue(verifyObject(
                ISlotRestriction,
                restrictions.BlockAll()))
        self.assertTrue(verifyObject(
                ISlotRestriction,
                restrictions.Permission()))
        self.assertTrue(verifyObject(
                ISlotRestriction,
                restrictions.CodeSourceName()))
        self.assertTrue(verifyObject(
                ISlotRestriction,
                restrictions.Content()))
        self.assertTrue(verifyObject(
                IContentSlotRestriction,
                restrictions.Content()))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RestrictionsTestCase))
    return suite
