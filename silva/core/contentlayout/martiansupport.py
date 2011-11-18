
import martian

import grokcore.component
import grokcore.view
from grokcore.view.meta.views import TemplateGrokker
from zope.component import provideAdapter
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from silva.core.contentlayout.interfaces import IBlockView
from silva.core.contentlayout.blocks import BlockView
from silva.core.contentlayout.templates import Template
from silva.core.contentlayout.templates.registry import registry


class RegisterTemplateGrokker(martian.ClassGrokker):
    martian.component(Template)

    def execute(self, factory, **kw):
        registry.register(factory)
        return True


class RegisterBlockViewGrokker(martian.ClassGrokker):
    martian.component(BlockView)
    martian.directive(grokcore.component.context)
    martian.directive(grokcore.view.layer, default=IDefaultBrowserLayer)
    martian.directive(grokcore.component.provides, default=IBlockView)

    def execute(self, factory, config, context, layer, provides, **kw):
        adapts = (context, layer)

        config.action(
            discriminator=('adapter', adapts, provides),
            callable=provideAdapter,
            args=(factory, adapts, provides))
        return True


class AssociateTemplateGrokker(TemplateGrokker):
    martian.component(Template)

    def has_render(self, factory):
        return False

    def has_no_render(self, factory):
        return True


class AssociateBlockViewGrokker(TemplateGrokker):
    martian.component(BlockView)
