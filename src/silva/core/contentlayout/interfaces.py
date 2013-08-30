# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

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
from silva.core.interfaces import IAddableContents, IIconResolver
from silva.core.interfaces import IVersion,  IVersionedObject
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


class IDesign(interface.Interface):
   """A design is a pluggable template used to render a content, that
   can contains blocks defined on the content.

   In the user interface, this is called a template. This extremely
   common term was not used in the code to prevent further confusion
   with already existing templates.
   """
   slots = interface.Attribute(
       u"A dictionary of slot used in the template associated to the design.")
   markers = interface.Attribute(
      u"List of customization markers to apply when the design is used.")

   def get_design_identifier():
      """Return a unique identifier for the template.
      """

   def get_all_design_identifiers(known=None):
      """Return every identifier used for this template as a list,
      meaning the identifier of this template, and of templates used
      by one.
      """

   def get_design_title():
      """Return template title to be used in the Silva Management Interface.
      """


class ICachableDesign(interface.Interface):
    """ Marker to tell if the design won't change and can be cached.
    """


class InvalidDesign(ValueError):
   pass


class ISlot(interface.Interface):
   """A slot is defined and contained inside a design. It defines an
   area in the design that can render blocks.
   """
   tag = interface.Attribute(
      u"HTML tag to use. It must be a block element.")
   css_class = interface.Attribute(
      u"CSS class to apply on the HTML tag.")

   def is_new_block_allowed(configuration, context):
       """Return True if a new block created with the given
       ``configuration`` would be allowed in this slot on the given
       ``context``.

       Return False if this is not authorized.
       """

   def is_existing_block_allowed(block, controller, context):
       """Return True if the existing ``block``, using the given
       ``controller`` is authorized in this slot on the given
       ``context``.

       Return False if this is not authorized.
       """

   def get_restrictions():
       """Return restrictions list set on this slot.
       """

   def get_new_restrictions(configuration):
       """Lookup for the given ``configuration`` an existing
       :py:interface:`~silva.core.contentlayout.interfaces.ISlotRestriction`.
       Return the restriction or None if no restriction is found.
       """

   def get_existing_restrictions(block):
       """Lookup for the given ``block`` an existing
       :py:interface:`~silva.core.contentlayout.interfaces.ISlotRestriction`.
       Return the restriction or None if no restriction is found.
       """


class InvalidSlot(KeyError):
   pass


class ISlotRestriction(interface.Interface):
   """Objects conforming this API are used to restrict which
   :py:interface:`~silva.core.contentlayout.interfaces.IBlock`, using
   which configuration or settings are allowed inside a given
   :py:interface:`~silva.core.contentlayout.interfaces.ISlot`.
   """

   def allow_configuration(configuration, slot, context):
       """Allow or disallow a not yet existing block that would be
       created using the given ``configuration`` to be added in the
       given ``slot``, located on the given ``context`` object.

       Must return True to allow the block, False to prevent it, and
       None if it has nothing to say.
       """

   def allow_controller(controller, slot, context):
        """Allow or disallow an existing block defined with the given
        ``controller`` to be moved or added to the given ``slot``,
        located on the given ``context`` object.

        Must return True to allow the block, False to prevent it, and
        None if it has nothing to say.
        """

   def apply_to(block_type):
       """Must return True if the restriction should apply the block
       defined by ``block_type``. ``block_type`` is the class of the
       block.
       """


class IContentSlotRestriction(ISlotRestriction):
   schema = interface.Attribute(
      u"Interface that the linked content must provides")


@grok.provider(IContextSourceBinder)
def design_identifier_source(context):
    registry = getUtility(IDesignLookup)

    def make_term(design):
       identifier = design.get_design_identifier()
       title = design.get_design_title()
       return Term(value=identifier, token=identifier, title=title)

    return Vocabulary(map(make_term, registry.lookup_design(None)))

@grok.provider(IFormSourceBinder)
def design_source(form):
   """Source vocabulary for design.
   """
   registry = getUtility(IDesignLookup)
   candidates = []
   blacklist_identifier = None
   current_identifier = None

   if isinstance(form, SMIAddForm):
      candidates = registry.lookup_design_by_addable(
         form.context, extensionRegistry.get_addable(form._content_type))
   else:
      candidates = registry.lookup_design(form.context)
      content = form.getContent()
      current = content.get_design()
      if current is not None:
         current_identifier = current.get_design_identifier()
      if IDesign.providedBy(content):
         # You cannot set a design used by this design here.
         blacklist_identifier = content.get_design_identifier()

   get_icon = IIconResolver(form.request).get_identifier_url

   def make_terms():
      for candidate in candidates:
         namespace = 'silva.core.contentlayout.designs'
         if IPageModelVersion.providedBy(candidate):
            namespace = 'silva.core.contentlayout.models'
         candidate_identifier = candidate.get_design_identifier()
         used_candidates = candidate.get_all_design_identifiers()
         if (blacklist_identifier is not None and
             blacklist_identifier in used_candidates and
             candidate_identifier != current_identifier):
            continue
         if used_candidates:
            identifier = (namespace, used_candidates[-1])
         else:
            identifier = ('default', namespace)
         icon = get_icon(identifier, default=namespace)
         yield Term(value=candidate,
                    token=candidate_identifier,
                    title=candidate.get_design_title(),
                    icon=icon)

   return Vocabulary(list(make_terms()))


class ITitledPage(ITitledContent):
    """Interface defining an add schema for a page.
    """
    design = schema.Choice(
        title=_(u"Template"),
        description=_(u"Select a template for your Page."),
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
   """A block is contained in a slot.

   In the user interface, this is called a component. This very common
   term was not used in the code in order to prevent confusion with
   already existing components.
   """


class IBlockSlot(IBlock, ISlot):
   """ A block usable as a slot inside a  page models.
   """
   identifier = interface.Attribute(
      u'Reprensent the slot id when used as a slot')

   def set_restrictions(restrictions):
       """Set the restrictions to apply on the slot.
       """

   def add_restriction(restriction, index=None):
       """Add the restriction (at the optional given order) to the slot.
       """

   def remove_restriction(restriction):
      """Remove the given restriction from the slot.
      """


class IBlockConfiguration(interface.Interface):
   """Describe a given block configuration for a given block, i.e. a
   unique scenario in which the block can be used.
   """
   identifier = interface.Attribute('Unique block identifier')
   title = interface.Attribute('Block configuration title')
   block = interface.Attribute('Associated block class')

   def get_icon(screen):
      """Return the icon used to represent this configuration.
      """

   def is_available(screen):
      """Return True if the configuration is available on this screen.
      """


class IBlockConfigurations(interface.Interface):
   """Return available block configurations for a given block,
   i.e. different scenarios in which the block can be used.
   """

   def get_by_identifier(identifier):
       """Return the associated configuration to the identifier.
       """

   def get_all():
      """Return all associated configurations with the block as a
      list.
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

    def get_slot_ids():
       """Return a list of all the slot identifiers available.
       """

    def get_block_ids():
       """Return a list of all the block identifiers available.
       """

    def get_block(block_id):
       """Return the block identified by block_id.
       """

    def get_slot(slot_id):
       """Return the slot identified by slot_id.
       """

    def get_all():
       """Return a list containing all the blocks themselves.
       """

    def add(slot_id, block, index=0):
       """Add the block to the slot identified by slot_id, return a
       new block_id. index defines the position in the slot the block
       is added.
       """

    def replace(block_id, new_block):
       """Replace the block identified by block_id with the new_block.
       """

    def move(slot_id, block_id, index):
       """Inside the slot identified by slot_id move the block
       identified by block_id to the given index.
       """

    def remove(block_id):
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
   silvaconf.resource('layout.css')
   silvaconf.resource('layout.js')
   silvaconf.resource('layout.components.js')
   silvaconf.resource('layout.modes.js')
   silvaconf.resource('layout.features.js')
   silvaconf.resource('layout.utils.js')


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
    """Defines how to lookup a design.
    """

    def lookup_design(context):
      """Lookup and return a list of available design.
      """

    def lookup_design_by_addable(context, addable):
      """Same as lookup but accept a silva content type as argument.
      """

    def lookup_design_by_name(name):
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
   blocks = schema.List(
      title=_(u"Components"),
      value_type=schema.Choice(
         title=_(u"Component type"),
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
      title=_(u"Template"),
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
      title=_(u"Template"),
      source=design_identifier_source)


class IDesignRestrictions(interface.Interface):

   restrictions = schema.Set(
      title=_(u"Restrictions"),
      value_type=schema.Object(schema=IDesignRestriction),
      required=False)


class IContentDefaultDesigns(interface.Interface):

   default_designs = schema.Set(
      title=_(u"Default templates"),
      value_type=schema.Object(schema=IDefaultDesignRule),
      required=False)


class IPageModel(IVersionedObject):
   """ A page model.

   This versioned content is usable as a design by other pages and
   models when it is published.
   """


class IPageModelVersion(IVersion, IPage, IDesign):
   """ A page model version.

   This version store the blocks and slots predefined in the model.
   """


class IPageModelFields(ITitledContent):
    """Interface defining an add schema for a page model.
    """
    design = schema.Choice(
       title=_(u"Template"),
       description=_(u"Select a template for your Page Model."),
       source=design_source)

    allowed_content_types = schema.Set(
       title=_(u"Allowed Content Types"),
       description=_(u"Only the selected content types will accept "
                     u"this Page Model as a template."),
       required=True,
       value_type=schema.Choice(
          source=content_type_source_without_placeholder))

    role = schema.Choice(
        title=_(u"Minimum role"),
        description=_(u"Only users with this role can utilise this "
                      u"Page Model."),
        source=editor_roles_source,
        required=False)


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
   design = interface.Attribute(u'Affected design')


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

