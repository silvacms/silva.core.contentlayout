# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope.interface.verify import verifyObject

from .. import restrictions, Slot, Block
from ..blocks.registry import get_block_configuration
from ..blocks.contents import ReferenceBlock
from ..interfaces import ISlot
from ..testing import FunctionalLayer


class SlotTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['silva.core.contentlayout']
        factory.manage_addMockupPage('page', 'Page')
        self.layer.login('manager')

    def test_slot_no_restrictions(self):
        """Test slot definition.
        """
        context = self.root.page.get_editable()
        slot = Slot()
        self.assertTrue(verifyObject(ISlot, slot))
        self.assertEqual(slot.tag, 'div')
        self.assertEqual(slot.css_class, None)

        configuration = lambda block: get_block_configuration(
            block, context).get_by_identifier()

        self.assertItemsEqual(
            list(slot.get_restrictions()),
            [])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(Block))),
            [])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(ReferenceBlock))),
            [])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(Block)),
            [])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(ReferenceBlock)),
            [])
        # As an author
        self.layer.login('author')
        self.assertEqual(
            slot.is_new_block_allowed(configuration(Block), context),
            True)
        self.assertEqual(
            slot.is_new_block_allowed(configuration(ReferenceBlock), context),
            True)

    def test_slot_restrict_content_block_all(self):
        """Test a slot that have a restriction on its content.
        """
        context = self.root.page.get_editable()
        content_restriction = restrictions.Content()
        all_restriction = restrictions.BlockAll()
        slot = Slot(
            tag='nav',
            css_class='navigation',
            restrictions=[content_restriction, all_restriction])

        configuration = lambda block: get_block_configuration(
            block, context).get_by_identifier()

        self.assertTrue(verifyObject(ISlot, slot))
        self.assertEqual(slot.tag, 'nav')
        self.assertEqual(slot.css_class, 'navigation')
        self.assertItemsEqual(
            list(slot.get_restrictions()),
            [content_restriction, all_restriction])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(Block))),
            [all_restriction])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(ReferenceBlock))),
            [content_restriction, all_restriction])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(Block())),
            [all_restriction])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(ReferenceBlock())),
            [content_restriction, all_restriction])

        # As an author
        self.layer.login('author')
        self.assertEqual(
            slot.is_new_block_allowed(configuration(Block), context),
            False)
        self.assertEqual(
            slot.is_new_block_allowed(configuration(ReferenceBlock), context),
            True)

    def test_slot_restrict_permission(self):
        """Test a slot that have a restriction on its permission.
        """
        context = self.root.page.get_editable()
        permission_restriction = restrictions.Permission(
            permission='silva.ManageSilvaContent')
        slot = Slot(
            restrictions=[permission_restriction])

        self.assertEqual(slot.tag, 'div')
        self.assertEqual(slot.css_class, None)

        configuration = lambda block: get_block_configuration(
            block, context).get_by_identifier()

        self.assertTrue(verifyObject(ISlot, slot))
        self.assertItemsEqual(
            list(slot.get_restrictions()),
            [permission_restriction,])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(Block))),
            [permission_restriction,])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(ReferenceBlock))),
            [permission_restriction,])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(Block())),
            [permission_restriction,])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(ReferenceBlock())),
            [permission_restriction,])

        # If I am a manager
        self.layer.login('manager')
        self.assertEqual(
            slot.is_new_block_allowed(configuration(Block), context),
            True)
        self.assertEqual(
            slot.is_new_block_allowed(configuration(ReferenceBlock), context),
            True)

        # If I am an author
        self.layer.login('author')
        self.assertEqual(
            slot.is_new_block_allowed(configuration(Block), context),
            False)
        self.assertEqual(
            slot.is_new_block_allowed(configuration(ReferenceBlock), context),
            False)

    def test_slot_restrict_permission_content_block_all(self):
        """Test a slot that have a restriction on its permission.
        """
        context = self.root.page.get_editable()
        permission_restriction = restrictions.Permission(
            permission='silva.ManageSilvaContent')
        content_restriction = restrictions.Content()
        all_restriction = restrictions.BlockAll()
        slot = Slot(
            restrictions=[permission_restriction,
                          content_restriction,
                          all_restriction])

        self.assertEqual(slot.tag, 'div')
        self.assertEqual(slot.css_class, None)

        configuration = lambda block: get_block_configuration(
            block, context).get_by_identifier()

        self.assertTrue(verifyObject(ISlot, slot))
        self.assertItemsEqual(
            list(slot.get_restrictions()),
            [permission_restriction, content_restriction, all_restriction])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(Block))),
            [permission_restriction, all_restriction])
        self.assertItemsEqual(
            list(slot.get_new_restrictions(configuration(ReferenceBlock))),
            [permission_restriction, content_restriction, all_restriction])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(Block())),
            [permission_restriction, all_restriction])
        self.assertItemsEqual(
            list(slot.get_existing_restrictions(ReferenceBlock())),
            [permission_restriction, content_restriction, all_restriction])

        # If I am a manager
        self.layer.login('manager')
        self.assertEqual(
            slot.is_new_block_allowed(configuration(Block), context),
            False)
        self.assertEqual(
            slot.is_new_block_allowed(configuration(ReferenceBlock), context),
            True)

        # If I am an author
        self.layer.login('author')
        self.assertEqual(
            slot.is_new_block_allowed(configuration(Block), context),
            False)
        self.assertEqual(
            slot.is_new_block_allowed(configuration(ReferenceBlock), context),
            False)
