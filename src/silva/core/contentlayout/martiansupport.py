
import martian
from martian.error import GrokError
from martian.scan import module_info_from_dotted_name
import os

from five import grok
from grokcore.view.meta.views import TemplateGrokker
from grokcore.view.templatereg import file_template_registry
from zope.component import provideAdapter
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from silva.core.contentlayout.interfaces import IBlockView
from silva.core.contentlayout.blocks import BlockView, Block
from silva.core.contentlayout.blocks.registry import \
    registry as block_registry
from silva.core.contentlayout.designs.design import Design, TemplateFile
from silva.core.contentlayout.designs.registry import \
    registry as design_registry


def default_name(component, module=None, **data):
    return component.__name__.lower()


class RegisterDesignGrokker(martian.ClassGrokker):
    martian.component(Design)
    extension = '.upt'

    def grok(self, name, factory, module_info, **kw):
        # Need to store the module info to look for a template
        factory.module_info = module_info
        return super(RegisterDesignGrokker, self).grok(
            name, factory, module_info, **kw)

    def execute(self, factory, **kw):
        if factory.template is None:
            self.associate_template(factory)

        design_registry.register(factory)
        return True

    def associate_template(self, factory):
        component_name = factory.__name__.lower()
        module_name, design_name = grok.template.bind(
            default=(None, None)).get(factory)
        if module_name is None:
            module_info = factory.module_info
            design_name = component_name
        else:
            module_info = module_info_from_dotted_name(module_name)
        design_dir = file_template_registry.get_template_dir(module_info)
        template_path = os.path.join(design_dir, design_name + self.extension)
        if not os.path.isfile(template_path):
            raise GrokError(u"Missing template %s for %s" % (
                    template_path, factory))
        factory.__template_path__ = template_path
        factory.template = TemplateFile(template_path)


class RegisterBlockViewGrokker(martian.ClassGrokker):
    martian.component(BlockView)
    martian.directive(grok.context)
    martian.directive(grok.layer, default=IDefaultBrowserLayer)
    martian.directive(grok.provides, default=IBlockView)

    def execute(self, factory, config, context, layer, provides, **kw):
        adapts = (context, layer)

        config.action(
            discriminator=('adapter', adapts, provides),
            callable=provideAdapter,
            args=(factory, adapts, provides))
        return True


class RegistryBlockGrokker(martian.ClassGrokker):
    martian.component(Block)
    martian.directive(grok.name, get_default=default_name)

    def execute(self, factory, name, **kw):
        block_registry.register(name, factory)
        return True


class AssociateBlockViewGrokker(TemplateGrokker):
    martian.component(BlockView)
