from five import grok
from zope.component import getMultiAdapter, queryMultiAdapter, getUtility

from silva.core.views import views as silvaviews
from silva.core.views.interfaces import ILayoutEditorLayer
from silva.core.interfaces import IContentLayout, IVersionedContentLayout
from silva.core.contentlayout.interfaces import IContentLayoutService
from silva.core.contentlayout.templates.interfaces import ILayoutView
from Products.Silva.SilvaObject import NoViewError

class ContentLayoutView(silvaviews.View):
    """ public "content.html" view for content layout objects
    This retrieves the ILayoutView for the current layout template and 
    returns it's __call__()
    """
    grok.context(IVersionedContentLayout)
    
    def update(self):
        super(ContentLayoutView, self).update()
        self.version = self.context.get_viewable()
    
    def render(self):
        """ rendering the layout requires the following:
          1) get the context's layout template
             depending on how the request is annotated, this will return
             either a LayoutView or LayoutEditView for the template
          2) the context will be the layout template, so add the model
             to the view
          3) call and return the view
        """
        sct = getUtility(IContentLayoutService)
        layout_name = self.version.get_layout_name()
        template = sct.get_template_by_name(layout_name)
        view = queryMultiAdapter( (template, self.request),
                                  interface=ILayoutView)
        if not view:
            msg = "No LayoutView for template %s defined"%(template)
            raise NoViewError, msg
        #need to fixup the context here.  the context needs to be the
        # content_layout content (i.e. an ISilvaObject)
        view.layout_template = view.context
        view.context = self.context
        view.version = self.version
        return view()
    
class NotEditableError(Exception):
    """this is raised if attempting to access the edit view of a
       non-editable (published or closed) object"""
    
class ContentLayoutEditView(ContentLayoutView):
    """ editor "content.html" view for content layout objects.
        essentially this is here to restrict access 
    """
    grok.layer(ILayoutEditorLayer)
    grok.require("silva.ReadSilvaContent")
    
    def update(self):
        super(ContentLayoutEditView, self).update()
        self.version = self.context.get_editable()
        if self.version is None:
            raise NotEditableError()
