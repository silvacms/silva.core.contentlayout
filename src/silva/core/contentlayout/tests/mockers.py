
from five import grok

from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.Version import Version

from silva.core import conf as silvaconf
from silva.core.contentlayout import interfaces


class MockPageVersion(Version):
    meta_type = 'Mock Page Version'
    grok.implements(interfaces.IPage)


class MockPage(VersionedContent):
    meta_type = 'Mock Page'
    silvaconf.version_class(MockPageVersion)
    grok.implements(interfaces.IPageAware)


class MockOtherPageVersion(Version):
    meta_type = 'Mock Other Page Version'
    grok.implements(interfaces.IPage)


class MockOtherPage(VersionedContent):
    meta_type = 'Mock Other Page'
    silvaconf.version_class(MockOtherPageVersion)
    grok.implements(interfaces.IPageAware)


def install_mockers(root):
    root.service_metadata.addTypesMapping(
        [MockPageVersion.meta_type], ('silva-content', 'silva-extra',))
    root.service_metadata.addTypesMapping(
        [MockOtherPageVersion.meta_type], ('silva-content', 'silva-extra',))
