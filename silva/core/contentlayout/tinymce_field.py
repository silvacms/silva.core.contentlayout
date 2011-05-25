from types import StringType, UnicodeType


from zope.interface import implements
from zope.component import getMultiAdapter
from zope.pagetemplate.pagetemplatefile import PageTemplateFile

from Products.Five import BrowserView
from App.class_init import InitializeClass
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from AccessControl import ClassSecurityInfo

from Products.Formulator.DummyField import fields
from Products.Formulator.FieldRegistry import FieldRegistry
from Products.Formulator.StandardFields import StringField
from Products.Formulator.Validator import StringValidator
from Products.Formulator.Widget import render_element,TextWidget

from silva.core.contentlayout.interfaces import (ITinyMCEField, 
                                                 ITinyMCEWidget, 
                                                 ITinyMCEValidator,
                                                 IFormulatorWidgetView)
from silva.core.contentlayout.interfaces import IRichTextCleanup


class TinyMCEWidgetView(object):
    """The rendered view of an ExternalSourcePart."""
    
    implements(IFormulatorWidgetView)

    template = PageTemplateFile('tinymce_widget.pt')
    
    def __init__(self, context):
        self.context = context

    def __call__(self, field, key, value, request):
        #send the content through an RE
        value = IRichTextCleanup(field).to_editor(value)
        if field.get_value('unicode') and not isinstance(value,UnicodeType):
            # use acquisition to get encoding of form
            value = unicode(value, field.get_form_encoding())
        return self.template(field=field,key=key,value=value,request=request)


class TinyMCEValidator(StringValidator):
    implements(ITinyMCEValidator)
    
    def validate(self, field, key, REQUEST):

        value = StringValidator.validate(self, field, key, REQUEST)
        #send the rich text through cleanup, preparing for storage
        value = IRichTextCleanup(field).from_editor(value)
        #make this unicode again, if needed.  lxml seems to operate and return
        # non-unicode chars
        if field.get_value('unicode') and not isinstance(value,UnicodeType):
            # use acquisition to get encoding of form
            value = unicode(value, field.get_form_encoding())
        return value


class TinyMCEWidget(TextWidget):
    implements(ITinyMCEWidget)
    property_names = TextWidget.property_names + ['tinyMCE_properties']
    tinyMCE_properties = fields.TextAreaField('tinyMCE_properties', title='tinyMCE Properties',width=80, height=10,\
                                              description='Customize tinyMCE Editor configuration options here. You may specify any valid configuration parameter.',\
                                              default = """
mode : "exact",
plugins : "silvalink, silvaimage, advlist, paste, table, silvaxhtmlxtras",
gecko_spellcheck: true,
paste_remove_spans: true,
paste_remove_styles: true,
paste_strip_class_attributes: "all",
editor_selector : "mceEditor",
theme : "advanced",
theme_advanced_toolbar_location: "top",
theme_advanced_buttons1: "bold,italic,underline,strikethrough,sub,sup,|,justifyleft,justifycenter,justifyright,justifyfull,|,formatselect,styleselect",
theme_advanced_buttons2 : "bullist,numlist,indent,outdent,|,link,unlink,anchor,image,|,cleanup,code,|,undo,redo,cut,copy,paste",
theme_advanced_buttons3: "tablecontrols,|,cite,abbr,acronym,|,charmap",
theme_advanced_blockformats: "p,h4,h5,h6,h3,address,pre,blockquote,code,h2",
theme_advanced_styles: "Quotation Right=pull-right;Quotation Left=pull-left",
table_inline_editing : false,
object_resizing : false,
height: 455,
width: '100%',
extended_valid_elements: "a[name|href|target|title|onclick|rel]",
silvaimage_styles: "numbers=numbers",
document_base_url: containerurl""", required = 1)
    
    def render(self, field, key, value, request):
        #place the widget rendering into a view, so that the
        #html is easier to manage/edit, and does not require a restart
        ad = IFormulatorWidgetView(self)
        return ad(field, key, value, request)
    
    def render_view(self, field, value, model=None, version=None):
        """pass the rich text through IRichTextCleanup, to prepare it for
           public viewing (this resolves urls, updates image attributes, etc)
           
           The parameters for this method are different than a standard 
           formulator field.  model and version were added to improve support
           for using this field in a code source (which has the correct
           model and version passed in already).  This bypasses the need to
           inspect request.model (which may be incorrect, in the case of
           a page asset pointing to a rich text code source)"""
        if value is None:
            return ''
        #send the rich text through cleanup, preparing for storage
        value = IRichTextCleanup(field).to_public(value, 
                                                  model=model,
                                                  version=version)
        return value


class TinyMCEField(StringField):
    implements(ITinyMCEField)
    
    security = ClassSecurityInfo()
    meta_type = "TinyMCEField"
    validator = TinyMCEValidator()
    widget = TinyMCEWidget()
    
    security.declareProtected('View', 'render_view')
    def render_view(self, value, model=None, version=None):
        """Render value to be viewed.
           Override Field.render_view to allow passing in model and version
           (improve support for cs_rich_text code source)
        """
        return self.widget.render_view(self, value, model, version)
InitializeClass(TinyMCEField)


FieldRegistry.registerField(TinyMCEField)
