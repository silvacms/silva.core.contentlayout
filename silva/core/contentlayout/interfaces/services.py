from silva.core.interfaces import ISilvaLocalService

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
