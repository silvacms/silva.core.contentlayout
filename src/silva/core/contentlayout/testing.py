# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Products.Silva.testing import SilvaLayer
import silva.core.contentlayout
from silva.core.contentlayout.tests.mocks import install_mocks
import transaction


class SilvaContentLayoutLayer(SilvaLayer):
    default_packages = SilvaLayer.default_packages + [
        'silva.core.contentlayout',
        ]

    def _install_application(self, app):
        super(SilvaContentLayoutLayer, self)._install_application(app)
        install_mocks(app.root)
        transaction.commit()


FunctionalLayer = SilvaContentLayoutLayer(silva.core.contentlayout)
