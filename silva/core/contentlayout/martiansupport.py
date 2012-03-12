
import martian
from martian.error import GrokError
from martian.scan import module_info_from_dotted_name
import os

import grokcore.component
import grokcore.view
from grokcore.view.meta.views import TemplateGrokker
from grokcore.view.templatereg import file_template_registry
from zope.component import provideAdapter
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from silva.core.contentlayout.interfaces import IBlockView
from silva.core.contentlayout.blocks import BlockView
from silva.core.contentlayout.templates.templates import Template, TemplateFile
from silva.core.contentlayout.templates.registry import registry


class RegisterTemplateGrokker(martian.ClassGrokker):
    martian.component(Template)
    extension = '.upt'

    def grok(self, name, factory, module_info, **kw):
        # Need to store the module info to look for a template
        factory.module_info = module_info
        return super(RegisterTemplateGrokker, self).grok(
            name, factory, module_info, **kw)

    def execute(self, factory, **kw):
        if factory.template is None:
            self.associate_template(factory)

        registry.register(factory)
        return True

    def associate_template(self, factory):
        component_name = factory.__name__.lower()
        module_name, template_name = grokcore.view.template.bind(
            default=(None, None)).get(factory)
        if module_name is None:
            module_info = factory.module_info
            template_name = component_name
        else:
            module_info = module_info_from_dotted_name(module_name)
        template_dir = file_template_registry.get_template_dir(module_info)
        template_path = os.path.join(
            template_dir, template_name + self.extension)
        if not os.path.isfile(template_path):
            raise GrokError(u"Missing template %s for %s" % (
                    template_path, factory))
        factory.__template_path__ = template_path
        factory.template = TemplateFile(template_path)


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


class AssociateBlockViewGrokker(TemplateGrokker):
    martian.component(BlockView)
