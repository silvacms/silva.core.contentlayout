
from five import grok
from zope import schema, interface
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IContextSourceBinder
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from silva.core import conf as silvaconf
from silva.core import interfaces
from silva.core.conf.interfaces import ITitledContent
from silva.translations import translate as _
from silva.ui.interfaces import ISilvaUIDependencies


class ISlot(interface.Interface):
   fill_in = interface.Attribute(u"fill-in stragegy")


class InvalidSlot(KeyError):
   pass


class ITemplate(interface.Interface):
   label = interface.Attribute(
       u"user-friendly name of template")
   description = interface.Attribute(
       u"a description of the template")
   slots = interface.Attribute(
       u"a dictionary of slot definition in the template")

   def update():
      """Method called before the template is rendered.
      """

class InvalidTemplate(ValueError):
   pass


@grok.provider(IContextSourceBinder)
def template_source(context):
    from silva.core.contentlayout.templates.registry import registry

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

class IBlock(interface.Interface):
   """Provide a block.
   """

class IBlockManager(interface.Interface):
    """Manage blocks.
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



class IBlockable(interfaces.IViewableObject):
    """Define a block that can be used in a page.
    """


class IReferenceBlock(IBlock):
    """Data stored for a reference block.
    """


class IBlockView(interface.Interface):
    """Render a given content for a IReferenceBlock.
    """
