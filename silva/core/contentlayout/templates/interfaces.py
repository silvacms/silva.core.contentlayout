from zope.interface import Interface

class ITemplate(Interface):
   
   def getName(self):
      """return user-friendly name of template"""

   def getDescription(self):
      """return description of template"""
        
   def getIcon(self):
      """return icon representing template"""

class IBaseView(Interface):
   """base interface for both public and edit views of 
      layout templates"""
   
   def inLayoutEditor():
      """returns True if the current request is actually "in"
         the layout editor (i.e. request provides IContentLayoutEditorLayer)
      """
      
   def renderParts(slot):
      """renders the parts for the slot
      """
      
   def renderPart(part, slot):
      """renders the part for the slot.  Based on the view's interface
         (view or edit view, below), will render using IContentLayoutPartView
         or IContentLayoutPartViewWidget
      """
      
   def renderPageTitle():
      """similar to renderPart, renders the page title either as 
         public view or edit viewwidget
      """
      
   def __call__(content_layout):
      """render the view.  ``content_layout`` is the IContentLayout object
         (e.g. Silva Page Version)
      """

class IPublicView(IBaseView):
   """Interface for public views of layout templates
   """

class IEditView(IBaseView):
   """Interface for edit views of layout templates
      (this view renders the content layout using the layout's
      template for display in the SMI"""


class IOneColumn(ITemplate):
   """Interface for basic 'one column' template"""

class ITwoColumn(ITemplate):
   """Interface for basic 'two column' template"""

