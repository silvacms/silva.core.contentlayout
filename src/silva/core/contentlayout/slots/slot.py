
from five import grok
from zope.component import getMultiAdapter
from grokcore.chameleon.components import ChameleonPageTemplate

from ..interfaces import IBoundBlockManager, ISlot, IEditionMode


class Slot(object):
    grok.implements(ISlot)

    def __init__(self, tag='div', css_class=None, restrictions=None):
        self.tag = tag
        self.css_class = css_class
        self._restrictions = restrictions or []

    def is_new_block_allowed(self, configuration, context):
        restriction = self.get_new_restriction(configuration)
        if restriction is not None:
            return restriction.allow_configuration(configuration, self, context)
        return True

    def is_existing_block_allowed(self, block, controller, context):
        restriction = self.get_existing_restriction(block)
        if restriction is not None:
            return restriction.allow_controller(controller, self, context)
        return True

    def get_new_restriction(self, configuration):
        return self._get_restriction(configuration.block)

    def get_existing_restriction(self, block):
        return self._get_restriction(block.__class__)

    def _get_restriction(self, block_type):
        for restriction in self._restrictions:
            if restriction.apply_to(block_type):
                return restriction
        return None


class SlotView(object):
    edit_template = ChameleonPageTemplate(filename='edit_slot.cpt')
    view_template = ChameleonPageTemplate(filename='view_slot.cpt')

    def __init__(self, slot, name, content, request):
        self.slot = slot
        self.slot_id = name
        self.tag = slot.tag
        self.css_id = 'slot-' + name
        self.css_class = slot.css_class
        self.content = content
        self.request = request

    def default_namespace(self):
        return {'slot': self,
                'request': self.request,
                'content': self.content}

    def namespace(self):
        return {}

    def blocks(self):
        return getMultiAdapter(
            (self.content, self.request),
            IBoundBlockManager).render(self.slot_id)

    def __call__(self):
        template = self.view_template
        if IEditionMode.providedBy(self.request):
            template = self.edit_template
        return template.render(self)
