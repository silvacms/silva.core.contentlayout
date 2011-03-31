from silva.core.interfaces import ISilvaLocalService, IContentLayout

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
        
    def register_templates(meta_type, templates):
        """set the allowed and default templates for ``meta_type``.
        ``templates`` is mapping of 
          {default: default template,
           allowed: [list of allowed templates]
           }
        """
    
    def get_allowed_templates_for_meta_type(meta_type):
        """return the list of allowed templates for ``meta_type``
        """
        
    def get_default_template_for_meta_type(meta_type):
        """return the default template for ``meta_type``
        """
    
    def get_formulator_template_tuples(meta_type):
        """returns a list of [utility name, template name, description] 
           for the purpose of generating lists of templates.  Useful for 
           zope 2 page templates.
           If meta_type is passed in, restricts the list to just those
             allowed for that meta_type
        """

    def get_template_tuples():
        """returns a generator of [utility name, template name, description] for the purpose
           of generating lists of templates.  Useful for zope 2 page templates
        """
 
    def get_templates(self):
        """returns a generator of [ utility name, template instance ]
        """
        
    def get_template_by_name(name):
        """get a ContentLayoutTemplate by it's utility name
        """
    
    def supports_content_layout(meta_type):
        """returns True if meta_type supports Content Layout
           (i.e. it implements IContentLayout or IVersionedContentLayout)
        """
        
    def get_supporting_meta_types():
        """returns a list of meta_types which support content layout
        """
        
class IStickyContentService(ISilvaLocalService):
    """A local service where sticky content mappings are stored.
       Sticky content are page assets are associated with individual
       content templates and will display on every page using that
       content template within the same container and below.
       
       Mappings are acquired from higher sticky services, so it is
       possible to add more sticky content at a lower level.  It is
       also possible to negate / prevent sticky content from appearing
       within a lower level.
    """
    
    def getStickyContentLayout(self, layout, create=True):
        """get the StickyContentLayout for `layout` (the name of the layout).
           if `create` and a StickyContentLayout does not exist, create one.
           (so this method can also be used to determine if sticky content
            exists (anywhere) for a layout)
        """
    
    def getBlockedPartsForLayout(self, layout):
        """returns the list of blocked parts for ``layout``
        """
    
    def getStickyContentForLayoutSlot(self, layout, slot):
        """get the sticky content in the `slot` in the `layout`.
           will return an empty list if there is no 
           sticky content
        """

    def hasStickyContentForLayout(self, layout):
        """return True if service has sticky content for `layout`, in 
           _any_ slot
        """
           
    def hasStickyContentForLayoutSlot(self, layout, slot):
        """return True if service has sticky content for `layout` in
           `slot`
        """
        
    def addStickyContent(self, template_name, part, slotname, beforepartkey=None):
        """Add a Sticky Content Part to the template `template_name`
        Sticky Content Parts are ContentLayoutParts which are
        instances of cs_page_asset (every sticky content is a page asset)
        """

    def blockAcquiredStickyContent(self, template_name, partkey):
        """block an acquired sticky content part for a template, given
        the parts key"""
        
    def unblockAcquiredStickyContent(self, template_name, partkey):
        """block an acquired sticky content part for a template, given
        the parts key
        """    

class IStickyContentLayout(IContentLayout):
    """StickyContentLayout stores the sticky content parts for a
       template.  Adds support for blocking parts"""

    def get_blocked_parts():
        """return the list of blocked part keys
        """
        
    def add_blocked_part(partkey):
        """add a parts (it's key) to the list of blocked parts
        """
        
    def remove_blocked_part(partkey):
        """remove a part (it's key) from the list of blocked parts
        """
    
__all__ = ['IContentLayoutService', 'IStickyContentService', 
           'IStickyContentLayout']
