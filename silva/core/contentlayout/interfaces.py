
from five import grok
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IContextSourceBinder
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from silva.core import conf as silvaconf
from silva.core import interfaces
from silva.core.conf.interfaces import ITitledContent
from silva.core.contentlayout.templates.registry import registry
from silva.translations import translate as _
from silva.ui.interfaces import ISilvaUIDependencies


@grok.provider(IContextSourceBinder)
def template_source(context):

    def make_term(template):
        return SimpleTerm(value=template,
                          token=template.__name__,
                          title=template.label)

    return SimpleVocabulary([make_term(t) for t in registry.lookup(context)])


class ITitledPage(ITitledContent):
    """Interface defining an add schema for a page.
    """
    template = schema.Choice(
        title=_(u"Template"),
        description=_(u"Select a template for your document."),
        source=template_source)


class IPage(interfaces.IViewableObject):
    """Define a page.
    """


class IPageBlock(interfaces.IViewableObject):
    """Define a block that can be used in a page.
    """


class IEditionMode(IDefaultBrowserLayer):
   """Mark the edition mode.

   Include extra CSS for the document in edit mode.
   """
   silvaconf.resource('editor.css')


class IEditorResources(ISilvaUIDependencies):
   """SMI plugin content-layout
   """
   silvaconf.resource('editor.js')