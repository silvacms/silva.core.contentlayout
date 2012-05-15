# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.Silva.testing import SilvaLayer
import silva.core.contentlayout
from silva.core.contentlayout.tests.mockers import install_mockers
import transaction


class SilvaContentLayoutLayer(SilvaLayer):
    default_packages = SilvaLayer.default_packages + [
        'silva.core.contentlayout',
        'silva.demo.contentlayout',
        ]

    def _install_application(self, app):
        super(SilvaContentLayoutLayer, self)._install_application(app)
        install_mockers(app.root)
        transaction.commit()


FunctionalLayer = SilvaContentLayoutLayer(silva.core.contentlayout)
