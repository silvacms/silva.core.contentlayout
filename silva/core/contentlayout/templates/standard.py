from five import grok

from silva.core.contentlayout.templates.template import Template, TemplateView
from silva.core.contentlayout.templates.interfaces import (IOneColumn, 
                                                           ITwoColumn)

@grok.global_utility
class OneColumn(Template):
    grok.implements(IOneColumn)
    grok.name('silva.core.contentlayout.templates.OneColumn')

    name = "One Column (standard)"
    description = "a simple one column layout"
    icon = "full.png"
    slotnames = ['maincontent']
    
class OneColumnView(TemplateView):
    grok.context(IOneColumn)
    grok.name(u'')
    
@grok.global_utility
class TwoColumn(Template):
    grok.implements(ITwoColumn)
    grok.name('silva.core.contentlayout.templates.TwoColumn')
    
    name = "Two Column (standard)"
    description = "a simple two column layout"
    icon = "fifty-fifty.png"
    slotnames = ['feature','panel']

class TwoColumnView(TemplateView):
    grok.context(ITwoColumn)
    grok.name(u'')
