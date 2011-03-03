from zope.interface import Interface, Attribute

class ITemplate(Interface):
   
   name = Attribute("user-friendly name of template")
   description = Attribute("a description of the template")
   icon = Attribute("relative path to an icom representing the template")
   title_heading_level = Attribute(("heading level for page titles, if the "
                                    "tempalte has a page title"))
   priority = Attribute(("The priority of the the template.is used to sort "
                         "lists of templates."))
   slotnames = Attribute("The list of slot names in this template")
   

class IOneColumn(ITemplate):
   """Interface for basic 'one column' template
   """

class ITwoColumn(ITemplate):
   """Interface for basic 'two column' template
   """
      
class ILayoutView(Interface):
   """interface for both public and edit views of 
      layout templates (the view is switched based on the layers in the request
   """
   
   def in_layout_editor():
      """returns True if the current request is actually "in"
         the layout editor (i.e. request provides IContentLayoutEditorLayer)
      """
      
   def render_parts(slot):
      """renders the parts for the slot
      """
      
   def render_part(part, slot):
      """renders the part for the slot.  Based on the view's interface
         (view or edit view, below), will render using IContentLayoutPartView
         or IContentLayoutPartViewWidget
      """
      
   def render_page_title():
      """similar to renderPart, renders the page title either as 
         public view or edit viewwidget
      """
      
   def __call__(content_layout):
      """render the view.  ``content_layout`` is the IContentLayout object
         (e.g. Silva Page Version)
      """
