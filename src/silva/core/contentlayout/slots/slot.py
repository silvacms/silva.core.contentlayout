from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate

from silva.core.contentlayout.interfaces import ISlot
from silva.core.contentlayout.interfaces import IEditionMode
from silva.core.contentlayout.interfaces import IBlockManager
from silva.core.contentlayout.blocks.registry import registry


class Slot(object):
    grok.implements(ISlot)

    def __init__(self, css_class=None, restrictions=None):
        self.css_class = css_class
        self._restrictions = restrictions or []

    def available_block_types(self, context):
        candidates = registry.all(context)
        factories = []
        for name, block_type in candidates:
            for restriction in self._restrictions:
                if restriction.apply_to(block_type):
                    if restriction.allow_block_type(block_type):
                        factories.append((name, block_type))
                    break
            else:
                factories.append((name, block_type))
        return factories

    def get_block_factory(self, name):
        block_factory = registry.lookup(name)
        if block_factory is None:
            return None, None

        for restriction in self._restrictions:
            if restriction.apply_to(block_factory):
                if restriction.allow_block_type(block_factory):
                    return block_factory, restriction
                return None, None

        return block_factory, None

    def is_block_allowed(self, block, context):
        for restriction in self._restrictions:
            if restriction.apply_to(block.__class__):
                return restriction.allow_block(block, context, self)
        return True

    def is_block_type_allowed(self, block_type, name=None):
        for restriction in self._restrictions:
            if restriction.apply_to(block_type):
                if name is None:
                    return restriction.allow_block_type(block_type)
                else:
                    return restriction.allow_block_type(block_type) and \
                        restriction.allow_name(name)
        return True


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
