# package

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller
from zope.interface import Interface
import tinymce_field

silvaconf.extensionName("silva.core.contentlayout")
silvaconf.extensionTitle("Silva Content Layout Base")

class Installer(DefaultInstaller):
    """Installer for the Silva Content Layout base extension.
    Override install, uninstall to add more actions.
    """

    def install(self, root):
        factory = root.manage_addProduct['silva.core.contentlayout']

        from services import ContentLayoutService as CLS
        from services import StickyContentService as SCS

        if CLS.default_service_identifier not in root.objectIds():
            factory.manage_addContentLayoutService(CLS.default_service_identifier)

        if SCS.default_service_identifier not in root.objectIds():
            factory.manage_addStickyContentService(SCS.default_service_identifier)
        super(Installer, self).install(root)

        from Products.Silva import roleinfo
        root.manage_permission('Add Silva Sticky Content Services', roleinfo.CHIEF_ROLES)


    def uninstall(self, root):
        from services import ContentLayoutService as CLS
        from services import StickyContentService as SCS

        to_remove = []
        if CLS.default_service_identifier in root.objectIds():
            to_remove.append(CLS.default_service_identifier)
        if SCS.default_service_identifier in root.objectIds():
            to_remove.append(SCS.default_service_identifier)
        if len(to_remove):
            root.manage_delObjects(to_remove)
        super(Installer, self).uninstall(root)

class IExtension(Interface):
    """Marker interface for our extension.
    """

install = Installer("silva.core.contentlayout", IExtension)

CLASS_CHANGES = {
    'Products.Silva.contentlayout.ServiceContentLayoutTemplates ContentLayoutTemplatesService':
    'silva.core.contentlayout.services ContentLayoutService',
    'Products.Silva.contentlayout.ServiceStickyContent StickyContentService':
    'silva.core.contentlayout.services StickyContentService',
    'Products.Silva.contentlayout.parts ExternalSourcePart':
    'silva.core.contentlayout.parts ExternalSourcePart',
    'Products.Silva.contentlayout.parts RichTextPart':
    'silva.core.contentlayout.parts RichTextPart',
    'Products.Silva.contentlayout.tinymce_field TinyMCEField':
    'silva.core.contentlayout.tinymce_field TinyMCEField',
    'Products.Silva.contentlayout.ServiceStickyContent StickyContentLayout':
    'silva.core.contentlayout.services StickyContentLayout',
    'Products.Silva.contentlayout.interfaces IRichTextExternalSource':
    'silva.core.contentlayout.interfaces.content IRichTextExternalSource',
    }