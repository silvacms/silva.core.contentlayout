from zope.interface import Interface

class IPartFactory(Interface):
    """interface for factory adapters, which return the appropriate
       Part object for a given IExternalSource type
       """
    
    def create(result_dict):
        """creates an IContentLayoutPart object, given the settings
        in result_dict
        """

class IPart(Interface):
    """An interface for objects that are "parts" in a content
       layout slot
    """
    
    def get_key():
        """returns a unique integer key identifying this external source
        """

class IExternalSourcePart(IPart):
    """An interface for objects that are "parts" in a content
       layout slot which represent external source data
    """
    
    def get_name():
        """return the name of the external source for this part
        """
        
    def set_config(config):
        """update this part's configuration dictionary,
        which stores the parameters for this external source part
        """
        
    def get_config():
        """return the configuration dictionary
        """

class IRichTextPart(IPart):
    """a part which stores rich text ONLY, e.g. it's external source object
       has _only_ a rich text (i.e. tinymce) field"""

class IPartEditWidget(Interface):    
    """ interface for adapters that render the edit view of 
        content layout parts (allowing authors to change
        the IPart
    """
    
    def __call__(model, mode, slotname, partkey, partconfig):
        """render the edit view for a contentlayout part.
        ``content`` the IContentLayout object (e.g. a Silva Page Version)
        ``mode`` 'add' or 'edit' (value rendered as a hidden input field on
                 form)
        ``slotname`` name of slot part is or will be placed in
        ``partkey`` the key for the part
        ``partconfig`` configuration (dictionary) for the part's instance
        ``submitButtonname`` the name of the submit button
        ``from_request`` boolean indicating the form has been submitted
                         (i.e. values are in the request)
        ``suppressFormTag`` boolean indicating whether this edit widget
                            should have a <form> tag around it, or should
                            be suppressed (i.e. displayed in the page asset
                            smi edit tab)
        ``submitOnTop`` boolean indicating whether to place a submit button
                        above the form inputs in addition to below
        """

class IRichTextExternalSource(Interface):
    """ marker interface for the "rich text" external source, manually add
        this to that external source"""

__all__ = ['IPartFactory', 'IPart', 'IExternalSourcePart', 'IRichTextPart',
           'IPartEditWidget', 'IRichTextExternalSource']