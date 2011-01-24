
from zope.interface import Interface

from silva.core.interfaces import ISilvaLocalService

class IVersionedContentLayout(Interface):
    """Marker interface for VersionedContent objects wich
       store versiones supporting content layout"""

class IContentLayout(Interface):
    """An interface to support complex content layouts.
       NOTE: for versionedcontent, the versions provide this interface"""
    
    def addPartToSlot(part, slot):
        """@part(IContentLayoutPart)
           @slot - name of a slot
           add the part to the slot with the given mane.
           May or may not require validation that the slot name
           is valid for the current layout"""
    
    def getPartsForSlot(slot):
        """@slot - name of a slot for the current layout
           returns the list of parts in the specified slot"""

class IContentLayoutService(ISilvaLocalService):
    """This service displays all of the registered content templates.
    
    It provides and interface to associate IContentLayout meta_types
    with a default content layout as well as the set of allowable
    content layouts for that meta type.
    """

    def manage_editMappings(REQUEST):
        """save the content type -> layout mappings (on the 'mappings'
        tab in the ZMI
        """
        
    def registerTemplates(meta_type, templates):
        """set the allowed and default templates for ``meta_type``.
        ``templates`` is mapping of 
          {default: default template,
           allowed: [list of allowed templates]
           }
        """
    
    def getAllowedTemplatesForMetaType(meta_type):
        """return the list of allowed templates for ``meta_type``
        """
        
    def getDefaultTemplateForMetaType(meta_type):
        """return the default template for ``meta_type``
        """
    
    def getFormulatorTemplateTuples(meta_type):
        """returns a list of [utility name, template name, description] 
           for the purpose of generating lists of templates.  Useful for 
           zope 2 page templates.
           If meta_type is passed in, restricts the list to just those
             allowed for that meta_type"""

    def getTemplateTuples():
        """returns a generator of [utility name, template name, description] for the purpose
           of generating lists of templates.  Useful for zope 2 page templates
        """
 
    def getTemplates(self):
        """returns a generator of [ utility name, template instance ]
        """
        
    def getTemplateByName(name):
        """get a ContentLayoutTemplate by it's utility name
        """
    
    def supportsContentLayout(meta_type):
        """returns True if meta_type supports Content Layout
           (i.e. it implements IContentLayout or IVersionedContentLayout)
        """
        
    def getSupportingMetaTypes():
        """returns a list of meta_types which support content layout
        """
