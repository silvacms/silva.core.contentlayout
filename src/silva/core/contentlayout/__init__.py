# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt
# package

from Products.Silva import roleinfo
from silva.core import conf as silvaconf
from silva.core.conf.installer import SystemExtensionInstaller
from zope.component import queryUtility

silvaconf.extension_name("silva.core.contentlayout")
silvaconf.extension_title("Silva Content Layout")
silvaconf.extension_system()


class ContentLayoutInstaller(SystemExtensionInstaller):
    default_permissions = {
        'Silva Page Model': roleinfo.CHIEF_ROLES,
        'Silva Page Model Version': roleinfo.CHIEF_ROLES}

    def is_installed(self, root, extension):
        return queryUtility(IContentLayoutService) is not None


install = ContentLayoutInstaller()


from .blocks import Block, BlockView, BlockController
from .interfaces import IContentLayoutService
from .designs.design import Design
from .slots import restrictions
from .slots.slot import Slot

__all__ = ['Design', 'Slot', 'Block', 'BlockView', 'BlockController',
           'restrictions', 'IContentLayoutService']
