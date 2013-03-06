# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.component import getMultiAdapter
from grokcore.chameleon.components import ChameleonPageTemplate

from ..interfaces import IBoundBlockManager, ISlot


class Slot(object):
    grok.implements(ISlot)

    def __init__(self, tag='div', css_class=None, restrictions=None):
        self.tag = tag
        self.css_class = css_class
        self._restrictions = restrictions or []

    def is_new_block_allowed(self, configuration, context):
        for rule in self.get_new_restrictions(configuration):
            status = rule.allow_configuration(configuration, self, context)
            if status is not None:
                return status
        return True

    def is_existing_block_allowed(self, block, controller, context):
        for rule in self.get_existing_restrictions(block):
            status = rule.allow_controller(controller, self, context)
            if status is not None:
                return status
        return True

    def get_restrictions(self):
        return list(self._restrictions)

    def get_new_restrictions(self, configuration):
        return self._get_restrictions(configuration.block)

    def get_existing_restrictions(self, block):
        return self._get_restrictions(block.__class__)

    def _get_restrictions(self, block_type):
        for restriction in self._restrictions:
            if restriction.apply_to(block_type):
                yield restriction


class SlotView(object):
    edit_template = ChameleonPageTemplate(filename='edit_slot.cpt')
    view_template = ChameleonPageTemplate(filename='view_slot.cpt')

    def __init__(self, name, slot, design, content):
        self.slot = slot
        self.slot_id = name
        self.tag = slot.tag
        self.css_id = 'slot-' + name
        self.css_class = slot.css_class or ''
        self.content = content
        self.design = design
        self.final = content is design.stack[-1]
        self.edition = self.design.edition and self.final

    def opening_tag(self):
        # This sucks a bit but this ain't doable in a template.
        if self.edition:
            return ''.join([
                    '<', self.tag, ' id="', self.css_id,
                    '" class="contentlayout-edit-slot ', self.css_class,
                    '" data-slot-id="', self.slot_id, '">'])
        return ''.join([
                '<', self.tag, ' id="', self.css_id,
                '" class="', self.css_class, '">'])

    def closing_tag(self):
        return ''.join(['</', self.tag, '>'])

    def default_namespace(self):
        return {'slot': self,
                'request': self.design.request,
                'content': self.content}

    def namespace(self):
        return {}

    def blocks(self):
        return getMultiAdapter(
            (self.content, self.design.request),
            IBoundBlockManager).render(self)

    def __call__(self):
        template = self.view_template
        if self.edition:
            template = self.edit_template
        return template.render(self)
