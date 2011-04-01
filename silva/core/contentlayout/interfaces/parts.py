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

    
class IRichTextExternalSource(Interface):
    """ marker interface for the "rich text" external source, manually add
        this to that external source"""

    
class IPartView(Interface):
    """ interface for adapters that render public views of
        content layout parts """
    
    def __call__(*args, **kw):
        """Part Views are callable adapters, meaning you get the
           part view adapter and then call it.
           Possible parameters:
           ``slot`` is the name of the slot
           ``content_layout`` is the IContentLayout model/object, e.g.
                              a Silva Page Version.
           Note that currently the part views do not use these
           parameters, but they are allowed to be passed in so that the API
           is the same for ICLPartView and PartViewWidget.
           """

        
class IPartViewWidget(Interface):
    """Interface for adapters that render the preview of an 
       IPart as a widget for the layout template's
       edit screen (in the smi)"""

    def render_part(interface):
        """render the part (i.e. self.context) using it's 
           IPartView, or an alternate passed in as ``interface``.
           This method is used by __call__"""
    
    def __call__(slot, content_layout):
        """Part Views Widgets are callable adapters, meaning you get the
           part view widget adapter and then call it.  The return value
           is a the html part preview wrapped within a container
           for the contentlayout interface, making it an eitable part
           ``slot`` is the name of the slot
           ``content_layout`` is the IContentLayout, e.g.
           a Silva Page Version"""

        
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

        
class ITitleView(IPartView):
    """ interface for adapters that render the public view of a page title.
        This is to enable page titles to be editable in the
        content layout editor.  The contentlayout interface treats
        page titles as a static part, which is why this inherits from
        IPartView"""

    
class ITitleViewWidget(IPartViewWidget):
    """ interface for adapters that render the public view widget
        of a page title.  This is to enable page titles to be editable in the
        content layout editor"""

    
class ITitleEditWidget(IPartEditWidget):
    """ interface for adapters that render the edit widget
        for a page title."""
    
    def __call__(self):
        """shows an input field allowing authors to edit the title
          of the contentlayout object.
          The parameters passed in to IPartEditWidget are not used, so
          this interface overrides __call__"""

        
class IStickySupport(Interface):
    """interface for adapters on parts which can be made sticky
       (i.e. they provide IPartSupportsSicky").  This adapter is
       used to get the sticky settings out of the part"""


__all__ = ['IPartFactory', 'IPart', 'IExternalSourcePart', 'IRichTextPart',
           'IPartEditWidget', 'IRichTextExternalSource', 'IPartView',
           'IPartViewWidget', 'ITitleView', 'ITitleViewWidget',
           'ITitleEditWidget', 'IStickySupport']