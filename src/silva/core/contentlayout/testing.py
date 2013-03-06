# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from Products.Silva.testing import SilvaLayer
from silva.core.contentlayout.tests.mockers import install_mockers
import silva.core.contentlayout
import transaction


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


FunctionalLayer = SilvaContentLayoutLayer(silva.core.contentlayout)

