from template import Template

class OneColumnTemplate(Template):
    grok.implements(IOneColumn)

    name = "One Column"
    description = "a simple one column layout"
    icon = None
    slotnames = ['maincontent']

class TwoColumnTemplate(Template):
    grok.implements(ITwoColumn)

    name = "Two Column"
    description = "a simple two column layout"
    icon = None
    slotnames = ['feature','panel']