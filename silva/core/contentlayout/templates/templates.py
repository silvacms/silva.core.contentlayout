
from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate
from zope.interface import Interface

from silva.core.contentlayout.templates.interfaces import ITemplate, ISlot
from silva.core.contentlayout.interfaces import IEditionMode
from silva.core.contentlayout.interfaces import IBlockInstances


class Slot(object):
    grok.implements(ISlot)

    def __init__(self, fill_in="vertical"):
        self.fill_in = fill_in


class SlotView(object):
    edit_template = ChameleonPageTemplate(filename='edit_slot.cpt')
    view_template = ChameleonPageTemplate(filename='view_slot.cpt')

    def __init__(self, slot, name, content, request):
        self.slot = slot
        self.slot_id = name
        self.slot_class = " ".join((name, 'slot-' + slot.fill_in))
        self.content = content
        self.request = request

    def default_namespace(self):
        return {'slot': self,
                'request': self.request,
                'content': self.content}

    def namespace(self):
        return {}

    def blocks(self):
        return IBlockInstances(self.content).render(
            self.slot_id, self.content, self.request)

    def __call__(self):
        template = self.view_template
        if IEditionMode.providedBy(self.request):
            template = self.edit_template
        return template.render(self)


class Template(object):
    """A Template.
    """
    grok.implements(ITemplate)
    grok.context(Interface)
    grok.provides(ITemplate)
    grok.baseclass()

    def __init__(self, content, request):
        self.content = content
        self.request = request

    def default_namespace(self):
        namespace = {}
        namespace['model'] = self
        namespace['content'] = self.content
        namespace['request'] = self.request
        return namespace

    def namespace(self):
        return {}

    def update(self):
        pass

    def __call__(self):
        self.update()
        return self.template.render(self)
