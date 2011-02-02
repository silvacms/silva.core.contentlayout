from zope.interface import Interface

class IFormulatorField(Interface):
    """a formulator field
    XXX should be in Products.Formulator.interfaces
    """
    def render():
        """render the field
        """

class IFormulatorWidget(Interface):
    """a widget for formulator fields
    XXX should be in Products.Formulator.interfaces
    """
    def render(field, key, value, request):
        """render the field
        """
    
    def render_view(field, value):
        """render the public view of the field
        """
        
class IFormulatorValidator(Interface):
    """ a validator for formulator fields
    XXX should be in Products.Formulator.interfaces
    """
    def validate(field, key, REQUEST):
        """validate the field
        """
        
class ITinyMCEField(IFormulatorField):
    """interface for the TinyMCE Formulator Field
    """

class ITinyMCEWidget(IFormulatorWidget):
    """interface for the TinyMCE Formulator Widget
    """
    
class ITinyMCEValidator(IFormulatorValidator):
    """interface for the TinyMCE Formulator Validator
    """

class IFormulatorWidgetView(Interface):
    """Formulator Widgets may choose to pass on the rendering
       of the edit widget (the widget's `render` method) to
       a Zope 3 view.  These views should implement this interface.
    """
    
    def __call__(field, key, value, request):
        """render the public view of a formulator widget
        """

__all__ = ['IFormulatorWidgetView','ITinyMCEValidator','ITinyMCEWidget',
           'ITinyMCEField', 'IFormulatorValidator', 'IFormulatorWidget',
           'IFormulatorField']
