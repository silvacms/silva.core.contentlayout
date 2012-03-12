
from chameleon.tales import StringExpr
from chameleon.codegen import template
from chameleon.astutil import Symbol

from silva.core.contentlayout.slots.slot import SlotView
from silva.core.contentlayout.interfaces import ITemplate
from silva.core.contentlayout.interfaces import InvalidTemplate, InvalidSlot


def slot_renderer(econtext, name):
    content = econtext.get('content')
    request = econtext.get('request')
    template = econtext.get('template')
    if not ITemplate.providedBy(template):
        raise InvalidTemplate(template)
    if name not in template.slots:
        raise InvalidSlot(name)
    return SlotView(template.slots[name], name, content, request)()


class SlotExpr(StringExpr):

    def __call__(self, target, engine):
        assignment = super(SlotExpr, self).__call__(target, engine)

        return assignment + template(
            "target = transform(econtext, target)",
            target = target,
            transform=Symbol(slot_renderer))
