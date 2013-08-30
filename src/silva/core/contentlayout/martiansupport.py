# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import sys
import os

import martian
from martian.error import GrokError
from martian.scan import module_info_from_dotted_name

from five import grok
from grokcore.view.meta.views import TemplateGrokker
from grokcore.view.templatereg import file_template_registry
from zope.component import provideAdapter
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.publisher.interfaces.browser import IHTTPRequest

from silva.core import conf as silvaconf
from silva.core.conf.utils import IconResourceFactory

from .blocks import BlockView, Block
from .blocks.registry import registry as block_registry
from .designs.design import Design, TemplateFile
from .designs.registry import registry as design_registry
from .interfaces import IBlockView

from Products.Silva.icon import registry as icon_registry


def default_name(component, module=None, **data):
    return component.__name__.lower()

def register_icon(self, config, cls, name, icons):
    """Register an icon.
    """
    if not icons:
        return

    base_path = os.path.dirname(sys.modules[cls.__module__].__file__)
    for key, icon_prefix in self.icon_prefix.items():
        icon_path = icons.get(key)
        if not icon_path:
            continue
        fs_path = os.path.join(base_path, icon_path)
        identifier = ''.join((
                icon_prefix,
                name.strip().replace(' ', '-'),
                os.path.splitext(icon_path)[1] or '.png'))

        factory = IconResourceFactory(name, fs_path)
        config.action(
            discriminator = ('resource', identifier, IHTTPRequest, Interface),
            callable = provideAdapter,
            args = (factory, (IHTTPRequest,), Interface, identifier))

        icon_name = "++resource++" + identifier
        icon_registry.register((self.icon_namespaces[key], name), icon_name)


class RegisterDesignGrokker(martian.ClassGrokker):
    martian.component(Design)
    martian.directive(silvaconf.icon)
    extension = '.upt'

    icon_namespaces = {
        None: 'silva.core.contentlayout.designs',
        'models': 'silva.core.contentlayout.models'}
    icon_prefix = {
        None: 'icon-designs-',
        'models': 'icon-models-'}

    def grok(self, name, factory, module_info, **kw):
        # Need to store the module info to look for a template
        factory.module_info = module_info
        return super(RegisterDesignGrokker, self).grok(
            name, factory, module_info, **kw)

    def execute(self, factory, icon, config, **kw):
        if factory.template is None:
            self.associate_template(factory)
        if icon is not None:
            identifier = factory.get_design_identifier()
            register_icon(self, config, factory, identifier, icon)
        design_registry.register_design(factory)
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
    martian.directive(silvaconf.icon)

    icon_namespaces = {
        None: 'silva.core.contentlayout.blocks'}
    icon_prefix = {
        None: 'icon-blocks-'}

    def execute(self, factory, name, icon, config, **kw):
        if icon is not None:
            register_icon(self, config, factory, name, icon)
        block_registry.register_block(name, factory)
        return True


class AssociateBlockViewGrokker(TemplateGrokker):
    martian.component(BlockView)


# Register default icons
for category, icon in (
    (('default', 'silva.core.contentlayout.designs'), 'design.png'),
    (('default', 'silva.core.contentlayout.models'), 'model.png')):
    icon_registry.register(
        category,
        '++static++/silva.core.contentlayout/' + icon)
