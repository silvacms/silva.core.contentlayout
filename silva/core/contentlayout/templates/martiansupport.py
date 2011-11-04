
import martian

from silva.core.contentlayout.templates import Template
from silva.core.contentlayout.templates.registry import registry
from grokcore.view.meta.views import TemplateGrokker


class RegisterTemplateGrokker(martian.ClassGrokker):
    martian.component(Template)

    def execute(self, factory, **kw):
        registry.register(factory)
        return True


class AssociateTemplateGrokker(TemplateGrokker):
    martian.component(Template)

    def has_render(self, factory):
        return False

    def has_no_render(self, factory):
        return True
