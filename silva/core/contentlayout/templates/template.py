from five import grok
from zope.component import getUtility

from silva.core.views.interfaces import ILayoutEditorLayer
from silva.core.contentlayout.interfaces import (IPartView, IPartViewWidget,
                                                 IContentLayoutService)
from silva.core.contentlayout.templates.interfaces import (ITemplate, 
                                                           ILayoutView)

class Template(object):
    """Base class for Content Layout templates.
       Templates are global utilities providing ITemplate which contain the 
       information for each layout template.  Subclasses of this should be 
       defined as global utilities.
       
       Public/Preview and Edit views are registered on these Templates.
    """

    grok.implements(ITemplate)
    grok.provides(ITemplate)
    grok.baseclass()

    name = "Base for Content Layout Templates"
    description = "Base for Content Layout Templates"
    icon = None
    #the heading level for page titles (if the layout has one)
    title_heading_level = 3
    #set default priority to low priority (higher number = lower priority)
    #in this way, institional templates can have higher priority
    priority = 50
    slotnames = []

class TemplateView(grok.View):
    grok.implements(ILayoutView)
    grok.provides(ILayoutView)
    grok.context(ITemplate)
    grok.name(u'')
    grok.baseclass()
    
    def __init__(self, context, request):
        super(TemplateView, self).__init__(context, request)
        self.content_layout = None
        self.in_layout_editor = False
        
    def update(self):
        self.in_layout_editor = ILayoutEditorLayer.providedBy(self.request)
        
    def get_parts(self, slot, wrapClass=None):
        """choose the interface depending on whether we are in 
        edit mode or not"""
        interface = IPartView
        if self.in_layout_editor:
            interface=IPartViewWidget

        #get the sticky content parts
        #ssc = self.content_layout.service_sticky_content.aq_inner
        #sticky_content = ssc.getStickyContentForLayoutSlot(
            #self.content_layout.getLayoutName(),
            #slot)

        before = []
        after = []
        #for sticky in sticky_content:
            #sticky_ad = IStickySupport(sticky)
            #rendered = self.renderPart(sticky, slot, wrapClass=wrapClass)
            #if sticky_ad.getPlacement() == 'above':
                #before.append(rendered)
            #else:
                #after.append(rendered)
        html = []
        for part in self.content_layout.get_parts_for_slot(slot):
            rendered = self.render_part(part, slot, interface, wrapClass=wrapClass)
            html.append(rendered)
        
        return [before, html, after]
    
    def render_part(self, part, slot, interface=IPartView, wrapClass=None):
        """this method will render the part using
           it's IPartViewWidget or IPartView"""
        return "part"
        ad = getMultiAdapter((part, self.request),
                             interface=interface)
        return ad(slot, self.content_layout, wrapClass=wrapClass)
    
    def render_parts(self, slot, wrapClass=None):
        parts = self.get_parts(slot, wrapClass=wrapClass)
        ret = ''
        for p in parts:
            ret += '\n'.join(p) + '\n'
            
        if self.in_layout_editor:
            ret = '<div class="bd">%s</div>'%ret

        #yui needs a non-empty body div
        return ret or ' '
    
    def render_page_title(self):
        """Depending on whether we're in the layout editor this method will 
           render the page title as an editable widget or the public view 
        """
        return "title"
        interface = IContentLayoutTitleView
        if IContentLayoutEditView.providedBy(self):
            interface=IContentLayoutTitleViewWidget
            
        ad = getMultiAdapter((self.content_layout, self.request),
                             interface=interface)
        return ad()
