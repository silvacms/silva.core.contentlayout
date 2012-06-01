# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope.component import queryUtility

from Products.Silva.testing import SilvaLayer
import silva.core.contentlayout
from silva.core.contentlayout.tests.mockers import install_mockers
import transaction
from silva.core.contentlayout.interfaces import IContentLayoutService


class SilvaContentLayoutLayer(SilvaLayer):
    default_products = SilvaLayer.default_products + [
        'SilvaExternalSources',
    ]
    default_packages = SilvaLayer.default_packages + [
        'silva.core.contentlayout',
        'silva.demo.contentlayout',
        ]

    def _install_application(self, app):
        super(SilvaContentLayoutLayer, self)._install_application(app)
        app.root.service_extensions.install('SilvaExternalSources')
        install_mockers(app.root)
        transaction.commit()


class SilvaContentLayoutLayerWithService(SilvaContentLayoutLayer):

    def _install_application(self, app):
        super(SilvaContentLayoutLayer, self)._install_application(app)
        app.root.service_extensions.install('silva.core.contentlayout')
        if queryUtility(IContentLayoutService) is None:
            factory = app.root.manage_addProduct['silva.core.contentlayout']
            factory.manage_addContentLayoutService()
        transaction.commit()


FunctionalLayer = SilvaContentLayoutLayer(silva.core.contentlayout)
FunctionalLayerWithService = SilvaContentLayoutLayerWithService(
    silva.core.contentlayout)

