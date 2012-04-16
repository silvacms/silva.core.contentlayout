
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
from silva.core import conf as silvaconf


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

import sys
from Products.Silva.icon import registry as icon_registry
from silva.core.conf.utils import IconResourceFactory
from zope.interface import Interface
from zope.publisher.interfaces.browser import IHTTPRequest


class RegistryBlockGrokker(martian.ClassGrokker):
    martian.component(Block)
    martian.directive(grok.name, get_default=default_name)
    martian.directive(silvaconf.icon)

    icon_namespace = 'silva.core.contentlayout.blocks'

    def register_icon(self, config, cls, block_name, icon_fs_path):
        if not icon_fs_path:
            return
        base_dir = os.path.dirname(sys.modules[cls.__module__].__file__)
        fs_path = os.path.join(base_dir, icon_fs_path)
        name = ''.join((
                'icon-blocks-',
                block_name.strip().replace(' ', '-'),
                os.path.splitext(icon_fs_path)[1] or '.png'))

        factory = IconResourceFactory(name, fs_path)
        config.action(
            discriminator = ('resource', name, IHTTPRequest, Interface),
            callable = provideAdapter,
            args = (factory, (IHTTPRequest,), Interface, name))

        resource_name = "++resource++" + name

        icon_registry.register((self.icon_namespace, block_name),
                               resource_name)
        cls.icon = resource_name

    def execute(self, factory, name, icon, config=None, **kw):
        if icon is not None and config is not None:
            self.register_icon(config, factory, name, icon)
        block_registry.register_block(name, factory)
        return True


class AssociateBlockViewGrokker(TemplateGrokker):
    martian.component(BlockView)
