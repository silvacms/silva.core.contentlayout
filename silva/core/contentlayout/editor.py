from five import grok
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.traversing.interfaces import ITraversable
from zope.interface import alsoProvides
from zope.component import getUtility

from Products.SilvaExternalSources import ExternalSource
from Products.SilvaExternalSources.interfaces import ICodeSource
from silva.core.views import views as silvaviews
from silva.core.views.traverser import UseParentByAcquisition
from silva.core.views.interfaces import ILayoutEditorLayer
from silva.core.layout.porto import porto
from silva.core.interfaces import (IVersionedContentLayout,
                                   IContentLayout)
from silva.core.contentlayout.interfaces import IContentLayoutService

class EditorTraversable(grok.MultiAdapter):
    """Traverser to the layout editor layer -- converts a content layout
       content-type's public view to the layout editor view.
       
       Adds the layer to the request if needed
    """
    grok.adapts(IContentLayout, IBrowserRequest)
    grok.implements(ITraversable)
    grok.name('layouteditor')
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def traverse(self, name, remaining):
        if not ILayoutEditorLayer.providedBy(self.request):
            alsoProvides(self.request, ILayoutEditorLayer)
        return UseParentByAcquisition()

class VersionedEditorTraversable(EditorTraversable):
    """so that this traverser can be used on the content objects, and not
       just the versions"""
    grok.adapts(IVersionedContentLayout, IBrowserRequest)

class LayoutEditHeaders(silvaviews.Viewlet):
    """defines a viewlet to add layout editor code to the html head of
       the content layout public rendering"""
    grok.viewletmanager(porto.HTMLHeadInsert)

class LayoutEditTab(grok.View):
    grok.context(IContentLayout)
    grok.require("silva.ReadSilvaContent")
    
    def default_namespace(self):
        ns = super(LayoutEditTab, self).default_namespace()
        editable = self.context.get_editable()
        sct = getUtility(IContentLayoutService)
        layout_name = editable.get_layout_name()

        ns['editable'] = editable
        ns['layout_name'] = layout_name
        ns['layout_template'] = sct.get_template_by_name(layout_name)
        ns['sct'] = sct
        
        mt = editable.get_content().meta_type
        allowed = sct.get_allowed_templates_for_meta_type(mt)
        templates = [ c for c in sct.get_sorted_templates() if 
                      c[0] != layout_name and c[0] in allowed ]
        ns['templates'] = templates
        return ns
    
    def get_external_source_list(self):
        """Return an ordered list of the External Sources within the
           current context.  Each item is a three-tuple of 
           [ priority, title, name, source ]"""
        sources = [ [s[1].priority(),s[1].title.encode('utf-8'),s[0], s[1]] \
                    for s in ExternalSource.availableSources(self.context.aq_inner) ]
        sources.sort()
        return sources

    def render_external_source_icon(self, source):
        """Render an External Source's icon.  If it is a codesource, it attempts
           to get the sources unique icon, otherwise the meta type's icon
           is used"""
        if ICodeSource.providedBy(source) and source.get_icon() and \
           source.get_icon().meta_type=="Image":
            icon = source.get_icon()
            return icon.tag()
        else:
            #XXX this is in ViewCode(?)
            return self.context.render_icon(source)
    