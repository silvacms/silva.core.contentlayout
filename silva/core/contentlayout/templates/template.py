from five import grok

from interfaces import ITemplate, IBaseView

class Template(object):
    """Base class for Content Layout templates.
       these need to inherit Acquisition.Implicit so they can be
       part of the acquisition hierarchy"""

    grok.implements(ITemplate)
    grok.baseclass()

    template = None
    name = "Base for Content Layout Templates"
    description = "Base for Content Layout Templates"
    icon = None
    #the heading level for page titles (if the layout has one)
    titleHeadingLevel = 3
    #set default priority to low priority (higher number = lower priority)
    #in this way, institional templates can have higher priority
    priority = 50
    slotnames = []

    def getName(self):
        return self.name

    def getPriority(self):
        return self.priority

    def getDescription(self):
        return self.description
    
    def getSlotNames(self):
        return self.slotnames[:]
    
class BaseView(object): #BrowserView):
    grok.implements(IBaseView)
    
    def __init__(self, context, request):
        #context is an IContentLayoutTemplate
        self.context = context
        self.request = request
        #filled when __call__ is called
        self.content_layout = None
        
    def inLayoutEditor(self):
        return IContentLayoutEditorLayer.providedBy(self.request)

    def getParts(self, slot, wrapClass=None):
        html = []
        
        """choose the interface depending on whether we are in 
        edit mode or not"""
        interface = IContentLayoutPartView
        if IContentLayoutEditView.providedBy(self):
            interface=IContentLayoutPartViewWidget

        #get the sticky content parts
        ssc = self.content_layout.service_sticky_content.aq_inner
        sticky_content = ssc.getStickyContentForLayoutSlot(
            self.content_layout.getLayoutName(),
            slot)

        before = []
        after = []
        for sticky in sticky_content:
            sticky_ad = IStickySupport(sticky)
            rendered = self.renderPart(sticky, slot, wrapClass=wrapClass)
            if sticky_ad.getPlacement() == 'above':
                before.append(rendered)
            else:
                after.append(rendered)
        
        for part in self.content_layout.getPartsForSlot(slot):
            rendered = self.renderPart(part, slot, interface, wrapClass=wrapClass)
            html.append(rendered)
        
        return [before, html, after]
    
    def renderParts(self, slot, wrapClass=None):
        parts = self.getParts(slot, wrapClass=wrapClass)
        ret = ''
        for p in parts:
            ret += '\n'.join(p) + '\n'
            
        if IContentLayoutEditView.providedBy(self):
            ret = '<div class="bd">%s</div>'%ret

        #yui needs a non-empty body div
        return ret or ' '
    
#    def renderPart(self, part, slot, interface = IContentLayoutPartView, wrapClass=None):
    def renderPart(self, part, slot, interface, wrapClass=None):
        """this method will render the part using
           it's IContentLayoutPartViewWidget or IContentLayoutPartView"""
            
        ad = getMultiAdapter((part, self.request),
                             interface=interface)
        return ad(slot, self.content_layout, wrapClass=wrapClass)
    
    def renderPageTitle(self):
        """Depending on whether self is an IContentLayoutEditView or an
           IContentLayoutView, this method will render the page title
           as an editable widget or the public view of the title"""
        interface = IContentLayoutTitleView
        if IContentLayoutEditView.providedBy(self):
            interface=IContentLayoutTitleViewWidget
            
        ad = getMultiAdapter((self.content_layout, self.request),
                             interface=interface)
        return ad()
    
    def __call__(self, content_layout):
        self.content_layout = content_layout
        self.request['model'] = self.content_layout.aq_inner.get_content()
        #stuff this into the context of the content_layout)
        self = self.__of__(content_layout)
        return self.template()
