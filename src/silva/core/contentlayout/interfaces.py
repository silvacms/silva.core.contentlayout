
from Acquisition import aq_parent

from five import grok
from zope import schema, interface
from zope.schema.interfaces import IContextSourceBinder
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.annotation import IAttributeAnnotatable
from zope.component import getUtility
from zope.component.interfaces import IObjectEvent, ObjectEvent

from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from silva.core.conf.schema import Vocabulary, Term
from silva.core.interfaces import IAddableContents
from silva.core.interfaces import IVersion,  IVersionedContent
from silva.core.interfaces import IViewableObject, ISilvaLocalService
from silva.core.views.interfaces import IVirtualSite
from silva.translations import translate as _
from silva.ui.interfaces import ISilvaUIDependencies
from zeam.form import silva as silvaforms
from zeam.form.silva.form.smi import SMIAddForm
from zeam.form.ztk.interfaces import IFormSourceBinder

from Products.Silva import roleinfo
from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva.icon import registry as iconRegistry


class ISlotRestriction(interface.Interface):
   """Restriction on the blocks a slot accepts
   """

   def allow_block_type(block_type):
      """ Allow this kind of block.
      """

   def allow_name(self, name):
      """ The name is arbitrary defined by the each type of blocks.

      For example for a code source, the name will be the identifier,
      e.g: cs_toc
      """

   def allow_block(block, context, slot):
      """ Allow this block instance in this context, on this slot.
      """


class IContentSlotRestriction(ISlotRestriction):
   interface = interface.Attribute(u"interface to limit usable content")


class ISlot(interface.Interface):
   css_class = interface.Attribute(u"CSS class to apply")
   restriction= interface.Attribute(u"ISlotRestriction restriction")


class InvalidSlot(KeyError):
   pass


class IDesign(interface.Interface):
   description = interface.Attribute(
       u"a description of the design")
   slots = interface.Attribute(
       u"a dictionary of slot definition in the design")
   markers = interface.Attribute(
      u"list of customization markers to apply in addition with the design")

   def update():
      """Method called before the design is rendered.
      """


class InvalidDesign(ValueError):
   pass


@grok.provider(IContextSourceBinder)
def design_identifier_source(context):
    registry = getUtility(IDesignLookup)

    def make_term(design):
        return Term(value=design.get_identifier(),
                    token=design.get_identifier(),
                    title=design.get_title())

    return Vocabulary(map(make_term, registry.lookup_design(None)))

@grok.provider(IFormSourceBinder)
def design_source(form):
   registry = getUtility(IDesignLookup)
   candidates = None
   base_url = IVirtualSite(form.request).get_root_url() + '/'

   if isinstance(form, SMIAddForm):
      candidates = registry.lookup_design_by_addable(
         form.context, extensionRegistry.get_addable(form._content_type))
   else:
      candidates = registry.lookup_design(form.context)

   def make_term(design):
      identifier = design.get_identifier()
      try:
         icon = base_url + iconRegistry.get_icon_by_identifier(
            ('silva.core.contentlayout.designs', identifier))
      except ValueError:
         icon = None
      return Term(value=design,
                  token=identifier,
                  title=design.get_title(),
                  icon=icon)

   return Vocabulary(map(make_term, candidates))


class ITitledPage(ITitledContent):
    """Interface defining an add schema for a page.
    """
    design = schema.Choice(
        title=_(u"Design"),
        description=_(u"Select a design for your document."),
        source=design_source)


def default_designs(form):
   registry = getUtility(IDesignLookup)
   design = None

   if isinstance(form, SMIAddForm):
      design = registry.default_design_by_addable(
         form.context, extensionRegistry.get_addable(form._content_type))
   else:
      design = registry.default_design(form.context)

   if design is not None:
      return design
   return silvaforms.NO_VALUE

PageFields = silvaforms.Fields(ITitledPage)
PageFields['design'].defaultValue = default_designs
PageFields['design'].mode = 'combobox'


class IPageAware(IViewableObject):
    """Define an interface that a content using a page should implement.
    """


class IPage(IAttributeAnnotatable):
   """Where the page is stored (that would be a version).
   """

   def get_design():
      """return the design using IDesignLookup.
      """

   def set_design(design):
      """set the design and triggers IDesign(De)associatedEvent events.
      """


class IBlock(interface.Interface):
   """A block.
   """


class IBlockSlot(IBlock, ISlot):
   """ A block usable as a slot for page models.
   """
   name = interface.Attribute('Slot id on the design')
   identifier = interface.Attribute('Reprensent the slot id '
                                    'when used as a slot')


class IBlockConfiguration(interface.Interface):
   identifier = interface.Attribute('Unique block identifier')
   title = interface.Attribute('Block configuration title')
   block = interface.Attribute('Associated block class')

   def get_icon(self, screen):
      """Return the icon.
      """

   def is_available(self, screen):
      """Return true if the configuration is available on this screen.
      """


class IBlockConfigurations(interface.Interface):
   """Return available block configuration (i.e. different scenarios
   in which the block can be used).
   """

   def get_by_identifier(identifier):
       """Return associated configuration to the identifier.
       """

   def get_all(self):
      """Return all associated configuration with the block.
      """


class IBlockController(interface.Interface):
   """Update block
   """

   def editable():
      """Return true if the block is editable.
      """

   def remove():
      """Remove associated data with the block.
      """

   def indexes():
      """Return list of defined anchors in the block.
      """

   def fulltext():
      """Return a list with the associated fulltext to the block.
      """

   def render():
      """Render the block.
      """


class IBlockManager(interface.Interface):
    """Manage blocks for a content.
    """

    def add(slot_id, block):
       """Add the block to the slot_it, return a new block_id.
       """

    def moveable(block_id, slot_id, content):
       """Return True if the block identified by block_id is moveable
       into the slot identified by slot_id on the given content.
       """

    def remove(block_id, content, request):
       """Remove the given block_id, on the given content, using the
       given request.
       """


class IBoundBlockManager(interface.Interface):
   pass



class IEditionResources(IDefaultBrowserLayer):
   """Mark the edition mode.

   Include extra CSS for the document in edit mode.
   """
   silvaconf.resource('editor.css')


class IEditorResources(ISilvaUIDependencies):
   """SMI plugin content-layout
   """
   silvaconf.resource('smi.css')
   silvaconf.resource('smi.js')


class IBlockable(IViewableObject):
    """Define a block that can be used in a page.
    """


class IReferenceBlock(IBlock):
    """Data stored for a reference block.
    """


class IBlockView(interface.Interface):
    """Render a given content for a IReferenceBlock.
    """

class ITextBlock(interface.Interface):
   """A block that only contains html text.
   """

class IDesignLookup(interface.Interface):
    """Defines how to lookup a design
    """

    def lookup_design(context):
      """Lookup and return a list of available design.
      """

    def lookup_design_by_addable(context, addable):
      """Same as lookup but accept a silva content type as argument.
      """

    def lookup_desgin_by_name(name):
       """Lookup a design by its grok name
       """

    def default_design(context):
       """Try to find a default design for this context or None.
       """

    def default_design_by_addable(context, addable):
       """Same as default_design but accept a silva content type as argument.
       """


@grok.provider(IContextSourceBinder)
def block_factory_source(context):
   from silva.core.contentlayout.blocks.registry \
       import registry as block_registry
   factories = block_registry.lookup_block(aq_parent(context))
   return Vocabulary(
      [Term(value=b.identifier, token=b.identifier, title=b.title)
       for b in factories])


class IBlockLookup(interface.Interface):
   """Lookup blocks.
   """

   def lookup_block(context):
      """Return all available block configurations.
      """

   def lookup_block_by_name(context, name):
      """Return the block configuration identified by the given name.
      """


class IBlockGroupLookup(interface.Interface):

   def lookup_block_by_name(view, name):
      """Lookup a group available for a view by its name.
      """

   def lookup_block_groups(view):
      """ Return a list of group with block configuration usuable in
      the given view.
      """


class IBlockGroup(interface.Interface):
   title = schema.TextLine(
      title=_(u"Title"),
      required=True)
   components = schema.List(
      title=_(u"Components"),
      value_type=schema.Choice(
         title=_(u"Block type"),
         required=True,
         source=block_factory_source),
      required=True)


class IBlockGroupsFields(interface.Interface):
   block_groups = schema.List(
      title=_(u"Groups"),
      value_type=schema.Object(IBlockGroup))


class IContentLayoutService(
   ISilvaLocalService, IDesignLookup, IBlockGroupLookup):
    """ContentLayout Service for Silva
    """


@apply
def editor_roles_source():
    roles = [Term(value=None,
                        token='',
                        title=_(u"-- Choose a role --"))]
    for role in roleinfo.AUTHOR_ROLES:
        roles.append(Term(value=role, token=role, title=_(role)))
    return Vocabulary(roles)

@grok.provider(IContextSourceBinder)
def all_content_type_source(context):
   terms = [Term(value=None,
                       token='',
                       title=_(u"-- Choose a content type --"))]
   for addable in extensionRegistry.get_addables(requires=[IPageAware,]):
      terms.append(Term(value=addable['name'],
                              token=addable['name'],
                              title=addable['name']))
   return Vocabulary(terms)

@grok.provider(IContextSourceBinder)
def content_type_source_without_placeholder(context):
   terms = []
   addables = IAddableContents(
      context.get_root()).get_all_addables(require=IPageAware)
   for addable in addables:
      terms.append(Term(value=addable,
                              token=addable,
                              title=addable))
   return Vocabulary(terms)


class IDesignContentRule(interface.Interface):
   """Rules bind together a design and a content
   """
   design = schema.Choice(
      title=_(u"Design"),
      source=design_identifier_source)
   content_type = schema.Choice(
      title=_(u"Content type"),
      source=all_content_type_source)


class IDesignRestriction(IDesignContentRule):
    """A design access rule limit the use of a design and a content type
    to a minimal role.
    """
    role = schema.Choice(
       title=_(u"Role"),
       source=editor_roles_source)


class IDefaultDesignRule(IDesignContentRule):
   """Default design per content type
   """
   # same fields as parent class but in reverse order
   content_type = schema.Choice(
      title=_(u"Content type"),
      source=all_content_type_source)
   design = schema.Choice(
      title=_(u"Design"),
      source=design_identifier_source)


class IDesignRestrictions(interface.Interface):

   restrictions = schema.Set(
      title=_(u"Restrictions"),
      value_type=schema.Object(schema=IDesignRestriction),
      required=False)


class IContentDefaultDesigns(interface.Interface):

   default_designs = schema.Set(
      title=_(u"Default designs"),
      value_type=schema.Object(schema=IDefaultDesignRule),
      required=False)


class IPageModel(IVersionedContent):
   """ A page model
   """


class IPageModelVersion(IVersion, IPage):
   """ A page model version
   """


class IPageModelFields(ITitledContent):
    """Interface defining an add schema for a page model.
    """
    design = schema.Choice(
       title=_(u"Design"),
       description=_(u"Select a design for your document."),
       source=design_source)

    allowed_content_types = schema.Set(
       title=_(u"Allowed Content Types"),
       description=_(u"Only the selected content types will accept "
                     u"it as a design"),
       required=True,
       value_type=schema.Choice(
          source=content_type_source_without_placeholder))


def all_page_content_types(form):
   addables = IAddableContents(
      form.context.get_root()).get_all_addables(require=IPageAware)
   return set(addables)

PageModelFields = silvaforms.Fields(IPageModelFields)
PageModelFields['allowed_content_types'].defaultValue = all_page_content_types
PageModelFields['design'].mode = 'combobox'


class IDesignEvent(IObjectEvent):
   """Base interface for design related events.
   """
   design = interface.Attribute('the design')


class IDesignAssociatedEvent(IDesignEvent):
   """Event triggered when a design is associated to a content.
   """


class IDesignDeassociatedEvent(IDesignEvent):
   """Event triggered when a design is deassociated to a content.
   """


class DesignEvent(ObjectEvent):
   interface.implements(IDesignEvent)

   def __init__(self, object, design):
      super(DesignEvent, self).__init__(object)
      self.design = design


class DesignAssociatedEvent(DesignEvent):
   interface.implements(IDesignAssociatedEvent)


class DesignDeassociatedEvent(DesignEvent):
   interface.implements(IDesignDeassociatedEvent)

