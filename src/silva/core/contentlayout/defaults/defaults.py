
from five import grok

from silva.core import conf as silvaconf
from silva.core.contentlayout import Template, Slot
from silva.fanstatic import need
from silva.translations import translate as _

from zope.publisher.interfaces.browser import IDefaultBrowserLayer


class OneColumn(Template):
    silvaconf.icon("one_column.png")
    grok.order(10)

    label = _(u"One Column (standard)")
    description = _(u"A simple one column layout")
    slots = {'main': Slot(fill_in="vertical")}


class ITwoColumnsResources(IDefaultBrowserLayer):
    silvaconf.resource('two_columns.css')


class TwoColumns(Template):
    silvaconf.icon("two_columns.png")
    grok.order(20)

    label = _(u"Two Columns (standard)")
    description = _(u"A simple two columns layout")
    slots = {'one': Slot(fill_in="vertical"),
             'two': Slot(fill_in="vertical")}


    def update(self):
        need(ITwoColumnsResources)
