# package

from silva.core import conf as silvaconf
from silva.core.conf.installer import DefaultInstaller
from zope.interface import Interface
import tinymce_field

silvaconf.extensionName("silva.core.contentlayout")
silvaconf.extensionTitle("Silva Content Layout Base")

from services import ContentLayoutService as CLS

class Installer(DefaultInstaller):
    """Installer for the Silva Content Layout base extension.
    Override install, uninstall to add more actions.
    """

    def install(self, root):
        factory = root.manage_addProduct['silva.core.contentlayout']

        if CLS.default_service_identifier not in root.objectIds():
            factory.manage_addContentLayoutService(CLS.default_service_identifier)
        super(Installer, self).install(root)
# once sticky content is created...
#    root.manage_permission('Add Silva Sticky Content Services', roleinfo.CHIEF_ROLES)


    def uninstall(self, root):
        if CLS.default_service_identifier in root.objectIds():
            root.manage_delObjects([CLS.default_service_identifier])
        super(Installer, self).uninstall(root)

class IExtension(Interface):
    """Marker interface for our extension.
    """

install = Installer("silva.core.contentlayout", IExtension)

CLASS_CHANGES = {
    'Products.Silva.contentlayout.ServiceContentLayout ContentLayoutTemplatesService':
    'silva.core.contentlayout.services ContentLayoutService',
    'Products.Silva.contentlayout.ServiceStickyContent StickyContentService':
    'silva.core.contentlayout.services StickyContentService',
    'Products.Silva.contentlayout.parts ExternalSourcePart':
    'silva.core.contentlayout.parts ExternalSourcePart',
    
    }