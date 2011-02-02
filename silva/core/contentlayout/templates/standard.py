from five import grok

from silva.core.contentlayout.templates.template import Template
from silva.core.contentlayout.templates.interfaces import (IOneColumn, 
                                                           ITwoColumn)

@grok.global_utility
class OneColumn(Template):
    grok.implements(IOneColumn)
    grok.name('silva.core.contentlayout.templates.OneColumn')

    name = "One Column"
    description = "a simple one column layout"
    icon = None
    slotnames = ['maincontent']

@grok.global_utility
class TwoColumn(Template):
    grok.implements(ITwoColumn)
    grok.name('silva.core.contentlayout.templates.TwoColumn')
    
    name = "Two Column"
    description = "a simple two column layout"
    icon = None
    slotnames = ['feature','panel']
