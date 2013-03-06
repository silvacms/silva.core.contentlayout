# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from chameleon.tales import StringExpr
from chameleon.codegen import template
from chameleon.astutil import Symbol

from silva.core.contentlayout.slots.slot import SlotView
from silva.core.contentlayout.interfaces import IDesign
from silva.core.contentlayout.interfaces import InvalidDesign, InvalidSlot


def slot_renderer(econtext, name):
    content = econtext.get('content')
    design = econtext.get('design')
    if not IDesign.providedBy(design):
        raise InvalidDesign(design)
    if name not in design.slots:
        raise InvalidSlot(name)
    slot = design.slots[name]
    return SlotView(name, slot, design, content)()


class SlotExpr(StringExpr):

    def __call__(self, target, engine):
        assignment = super(SlotExpr, self).__call__(target, engine)

        return assignment + template(
            "target = transform(econtext, target)",
            target = target,
            transform=Symbol(slot_renderer))
