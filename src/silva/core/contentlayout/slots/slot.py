
from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate

from silva.core.contentlayout.interfaces import ISlot
from silva.core.contentlayout.interfaces import IEditionMode
from silva.core.contentlayout.interfaces import IBlockManager


class Slot(object):
    grok.implements(ISlot)

    def __init__(self, css_class=None):
        self.css_class = css_class


class SlotView(object):
    edit_template = ChameleonPageTemplate(filename='edit_slot.cpt')
    view_template = ChameleonPageTemplate(filename='view_slot.cpt')

    def __init__(self, slot, name, content, request):
        self.slot = slot
        self.slot_id = name
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
        return IBlockManager(self.content).render(
            self.slot_id, self.content, self.request)

    def __call__(self):
        template = self.view_template
        if IEditionMode.providedBy(self.request):
            template = self.edit_template
        return template.render(self)
