# -*- coding: utf-8 -*-
# Copyright (c) 2012  Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface

from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.Version import Version

from silva.core import conf as silvaconf
from Products.Silva.silvaxml import xmlexport
from ..silvaxml.xmlexport import BasePageProducer
from ..designs.design import DesignAccessors
from .. import Design, Slot
from .. import interfaces


class MockupPageVersion(DesignAccessors, Version):
    meta_type = 'Mockup Page Version'
    grok.implements(interfaces.IPage)


class MockupPage(VersionedContent):
    meta_type = 'Mockup Page'
    silvaconf.version_class(MockupPageVersion)
    grok.implements(interfaces.IPageAware)


class MockOtherPageVersion(DesignAccessors, Version):
    meta_type = 'Mock Other Page Version'
    grok.implements(interfaces.IPage)


class MockOtherPage(VersionedContent):
    meta_type = 'Mock Other Page'
    silvaconf.version_class(MockOtherPageVersion)
    grok.implements(interfaces.IPageAware)


class MockupPageProducer(xmlexport.VersionedContentProducer):
    grok.adapts(MockupPage, Interface)

    def sax(self):
        self.startElement('page', {'id': self.context.id})
        self.workflow()
        self.versions()
        self.endElement('page')


class MockupPageVersionProducer(BasePageProducer):
    grok.adapts(MockupPageVersion, Interface)

    def sax(self):
        self.startElement('content', {'version_id': self.context.id})
        self.metadata()
        self.design()
        self.endElement('content')


class MockDesign(Design):
    grok.name('adesign')
    grok.title('A Design for testing')

    slots = {
        'one': Slot(),
        'two': Slot()
    }


def install_mockers(root):
    root.service_metadata.addTypesMapping(
        [MockupPageVersion.meta_type], ('silva-content', 'silva-extra',))
    root.service_metadata.addTypesMapping(
        [MockOtherPageVersion.meta_type], ('silva-content', 'silva-extra',))
