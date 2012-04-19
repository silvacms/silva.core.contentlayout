
from chameleon.tales import StringExpr
from chameleon.codegen import template
from chameleon.astutil import Symbol

from silva.core.contentlayout.slots.slot import SlotView
from silva.core.contentlayout.interfaces import IDesign
from silva.core.contentlayout.interfaces import InvalidDesign, InvalidSlot


def slot_renderer(econtext, name):
    content = econtext.get('content')
    request = econtext.get('request')
    design = econtext.get('design')
    edit_slot = econtext.get('design_edition_mode')
    if not IDesign.providedBy(design):
        raise InvalidDesign(design)
    if name not in design.slots:
        raise InvalidSlot(name)
    edition = edit_slot and design in edit_slot
    return SlotView(design.slots[name], name, content, request)(edition)


class SlotExpr(StringExpr):

    def __call__(self, target, engine):
        assignment = super(SlotExpr, self).__call__(target, engine)

        return assignment + template(
            "target = transform(econtext, target)",
            target = target,
            transform=Symbol(slot_renderer))
