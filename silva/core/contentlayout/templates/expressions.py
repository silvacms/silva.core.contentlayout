
import re

from five import grok
from chameleon.core import types
from chameleon.zpt import expressions

from silva.core.contentlayout.templates.templates import SlotView
from silva.core.contentlayout.templates.interfaces import ITemplate
from silva.core.contentlayout.templates.interfaces import (
    InvalidModel, InvalidSlot)


def slot_traverser(context, request, model, name):
    if not ITemplate.providedBy(model):
        raise InvalidModel(model)
    if name not in model.slots:
        raise InvalidSlot(name)
    return SlotView(model.slots[name], name, context, request)()


class SlotTranslator(expressions.ExpressionTranslator):
    slot_regex = re.compile(r'^[A-Za-z][A-Za-z0-9_\.-]*$')

    symbol = '_get_model_slot'

    def translate(self, string, escape=None):
        if self.slot_regex.match(string) is None:
            raise SyntaxError(
                "%s is not a valid content slot name." % string)

        value = types.value(
            "%s(content, request, model, '%s')" % (self.symbol, string))
        value.symbol_mapping[self.symbol] = slot_traverser
        return value


grok.global_utility(SlotTranslator, name='slot')
