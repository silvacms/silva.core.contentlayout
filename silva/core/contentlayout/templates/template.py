from five import grok
from zope.component import getUtility, getMultiAdapter

from silva.core.views.interfaces import ILayoutEditorLayer
from silva.core.contentlayout.interfaces import (IPartView, IPartViewWidget,
                                                 IContentLayoutService,
                                                 ITitleView, ITitleViewWidget,
                                                 IStickyContentService,
                                                 IStickySupport)
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
    title_heading_level = 1
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
        self.version = None
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
        ssc = getUtility(IStickyContentService, context=self.version)
        sticky_content = ssc.getStickyContentForLayoutSlot(
            self.version.get_layout_name(),
            slot)

        before = []
        after = []
        for sticky in sticky_content:
            sticky_ad = IStickySupport(sticky)
            #DO NOT send the "interface" through to sticky content.  it is
            # ALWAYS IPartView (NEVER IPartViewWidget)
            rendered = self.render_part(sticky, slot, 
                                        wrapClass=wrapClass)
            if sticky_ad.get_placement() == 'above':
                before.append(rendered)
            else:
                after.append(rendered)
        html = []
        for part in self.version.get_parts_for_slot(slot):
            rendered = self.render_part(part, slot, interface, 
                                        wrapClass=wrapClass)
            html.append(rendered)
        
        return [before, html, after]
    
    def render_part(self, part, slot, interface=IPartView, wrapClass=None):
        """this method will render the part using
           it's IPartViewWidget or IPartView"""
        ad = getMultiAdapter((part, self.request),
                             interface=interface)
        ad.contentlayout = self.version
        ad.slot = slot
        ad.wrapClass = wrapClass
        return ad()
    
    def render_parts(self, slot, wrapClass=None):
        part_sections = self.get_parts(slot, wrapClass=wrapClass)
        ret = ''
        for p in part_sections:
            ret += '\n'.join(p) + '\n'
            
        if self.in_layout_editor:
            ret = '<div class="bd">%s</div>'%ret

        #yui needs a non-empty body div
        return ret or ' '
    
    def render_page_title(self):
        """Depending on whether we're in the layout editor this method will 
           render the page title as an editable widget or the public view 
        """
        interface = ITitleView
        if ILayoutEditorLayer.providedBy(self.request):
            interface=ITitleViewWidget
            
        ad = getMultiAdapter((self.version, self.request),
                             interface=interface)
        return ad()
