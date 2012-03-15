
from five import grok
from zope import schema, interface
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IContextSourceBinder
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.annotation import IAttributeAnnotatable

from silva.core import conf as silvaconf
from silva.core import interfaces
from silva.core.conf.interfaces import ITitledContent
from silva.translations import translate as _
from silva.ui.interfaces import ISilvaUIDependencies

from Products.Silva import roleinfo


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


class IPageAware(interfaces.IViewableObject):
    """Define an interface that a content using a page should implement.
    """

class IPage(IAttributeAnnotatable):
   """Where the page is stored (that would be a version).
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


class ITemplateLookup(interface.Interface):
    """ Defines how to lookup a template
    """
    def lookup(context):
      """ lookup and return a list of available template
      """


class ITemplateService(interfaces.ISilvaService, ITemplateLookup):
    """ Template Service for Silva
    """


@apply
def silva_role_source():
    roles = []
    for role in roleinfo.ASSIGNABLE_ROLES:
        roles.append(SimpleTerm(value=role, token=role, title=role))
    return SimpleVocabulary(roles)

@grok.provider(IContextSourceBinder)
def content_type_source(context):
   addables = interfaces.IAddableContents(
      context.get_root()).get_all_addables(require=IPageAware)
   return SimpleVocabulary([SimpleTerm(value=addable,
                              token=addable,
                              title=addable)
                            for addable in addables])


class ITemplateContentRule(interface.Interface):
   """Rules bind together a template and a content
   """
   template = schema.Choice(title=_(u"Template"),
                            source=template_source)
   content_type = schema.Choice(title=_(u"Content type"),
                                source=content_type_source)


class ITemplateAccessRule(ITemplateContentRule):
    """A template access rule limit the use of a template and a content type
    to a minimal role.
    """
    role = schema.Choice(title=_(u"Role"),
                         source=silva_role_source)


class IDefaultTemplateRule(ITemplateContentRule):
   """Default template per content type
   """


class ITemplateAccessRules(interface.Interface):

   rules = schema.Set(
      title=_(u"Access rules"),
      value_type=schema.Object(schema=ITemplateAccessRule),
      required=True)


class IContentDefaultTemplates(interface.Interface):

   default_templates = schema.Set(
      title=_(u"Default templates"),
      value_type=schema.Object(schema=IDefaultTemplateRule),
      required=True)

