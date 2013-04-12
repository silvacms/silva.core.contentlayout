# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import re
import uuid

from AccessControl import getSecurityManager

from five import grok
from persistent import Persistent
from zope.interface import Interface
from zope.publisher.interfaces.http import IHTTPRequest
from zope import schema
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zeam.form.ztk import EditAction
from grokcore.chameleon.components import ChameleonPageTemplate

from silva.core import conf as silvaconf
from silva.translations import translate as _
from zeam.form import silva as silvaforms

from Products.SilvaExternalSources.interfaces import availableSources
from Products.Silva.ExtensionRegistry import extensionRegistry

from .manager import Block, BlockController
from ..interfaces import IPageModelVersion, IBlockSlot, IBlockable
from ..slots.slot import Slot, SlotView
from ..slots import restrictions as restrict


class BlockSlot(Persistent, Slot, Block):
    grok.implements(IBlockSlot)
    grok.name('slot')
    grok.title(_('Slot'))
    grok.context(IPageModelVersion)
    grok.order(50)
    silvaconf.icon('slot.png')

    def __init__(self, identifier=None, tag='section', css_class='',
                 restrictions=None):
        Slot.__init__(self, tag=tag,
                      css_class=css_class,
                      restrictions=restrictions)
        if identifier is None:
            identifier = unicode(uuid.uuid1())
        self.identifier = identifier

    def set_restrictions(self, restrictions):
        self._restrictions = list(restrictions)

    def add_restriction(self, restriction, index=None):
        if index is None:
            self._restrictions.append(restriction)
        else:
            self._restrictions.insert(index, restriction)
        self._p_changed = True

    def remove_restriction(self, restriction):
        try:
            self._restrictions.remove(restriction)
            self._p_changed = True
        except ValueError:
            pass


@grok.provider(IContextSourceBinder)
def content_type_source(context):
    terms = [SimpleTerm(value=IBlockable,
                        token='',
                        title=_(u"No restriction"))]
    for addable in extensionRegistry.get_addables(requires=[IBlockable,]):
        terms.append(
            SimpleTerm(
                value=addable['interfaces'][0],
                token=addable['name'],
                title=addable['name']))
    return SimpleVocabulary(terms)

@grok.provider(IContextSourceBinder)
def code_source_source(context):
    terms = []
    for identifier, _ in availableSources(context.get_root()):
        terms.append(SimpleTerm(value=identifier,
                                title=identifier,
                                token=identifier))
    return SimpleVocabulary(terms)


class IBlockSlotFields(Interface):

    identifier = schema.TextLine(
        title=_(u"Slot identifier"),
        description=_(
            u"This identifier should uniquely identify the new sub-slot, "
            u"and will be used to refer the sub-slot to store components. "
            u"Only letters and numbers are allowed."),
        required=True)

    tag = schema.TextLine(
        title=_(u'HTML tag'),
        description=_(u"HTML tag to use to create the slot."),
        required=True,
        default=u'section')

    css_class = schema.TextLine(
        title=_(u'CSS class(es)'),
        description=_(
            u'Whitespace delimited CSS classes to apply on the slot.'),
        required=False,
        default=u'')

    # code source restriction
    cs_whitelist = schema.Set(
        title=_(u"Code source whitelist"),
        description=_(
            u"If any code sources are selected, it will be the only ones "
            u"addable to the slot."),
        value_type=schema.Choice(
            title=_(u'name'),
            source=code_source_source),
        required=False,
        default=set())

    cs_blacklist = schema.Set(
        title=_(u"Code source blacklist"),
        description=_(
            u"If any code sources are selected, it will be the only ones "
            u"not addable to the slot."),
        value_type=schema.Choice(
            title=_(u'name'),
            source=code_source_source),
        required=False,
        default=set())

    # content restriction
    content_restriction = schema.Choice(
        title=_(u"Content type"),
        description=_(
            u"Only the selected Silva content types will be addable "
            u"to the slot using the site content component."),
        source=content_type_source,
        required=False)

    # block all restriction
    block_all = schema.Bool(
        title=_(u"Block all others"),
        description=_(
            u"Any code sources or Silva content types not explicitly allowed "
            u"by a previous option won't be addable to the slot if this "
            u"option is checked."),
        required=False,
        default=False)


class BlockSlotController(BlockController):
    grok.adapts(IBlockSlot, Interface, IHTTPRequest)

    edit_template = ChameleonPageTemplate(
        filename="edit_slot.cpt")

    def editable(self):
        return True

    def namespace(self):
        return {}

    def default_namespace(self):
        return {"slot": self,
                "request": self.request}

    def render(self, view=None):
        if view is not None and not view.final:
            design = view.design
            next_content = design.stack[design.stack.index(view.content) + 1]
            next_view = SlotView(
                self.block.identifier, self.block, design, next_content)
            return next_view()
        return self.edit_template.render(self)

    def get_identifier(self):
        return self.block.identifier

    def set_identifier(self, value):
        self.block.identifier = value

    def get_tag(self):
        return self.block.tag

    def set_tag(self, tag):
        self.block.tag = tag

    def get_css_class(self):
        return self.block.css_class

    def set_css_class(self, css_class):
        self.block.css_class = css_class

    def get_cs_whitelist(self):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            return set()
        return restriction.allowed

    def set_cs_whitelist(self, whitelist):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            self.block.add_restriction(
                restrict.CodeSourceName(allowed=whitelist), index=0)
        else:
            restriction.allowed = whitelist

    def get_cs_blacklist(self):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            return set()
        return restriction.disallowed

    def set_cs_blacklist(self, blacklist):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            self.block.add_restriction(
                restrict.CodeSourceName(disallowed=blacklist), index=0)
        else:
            restriction.disallowed = blacklist

    def get_content_restriction(self):
        restriction = self._find_restriction_with_type(restrict.Content)
        if restriction is None:
            return None
        return restriction.schema

    def get_content_restriction_name(self):
        schema = self.get_content_restriction()
        if schema is not None:
            for addable in extensionRegistry.get_addables(requires=[IBlockable,]):
                if schema is addable['interfaces'][0]:
                    return addable['name']
        return None

    def set_content_restriction(self, schema):
        restriction = self._find_restriction_with_type(restrict.Content)
        if restriction is None:
            self.block.add_restriction(restrict.Content(schema), index=0)
        else:
            restriction.schema = schema

    def get_block_all(self):
        restriction = self._find_restriction_with_type(restrict.BlockAll)
        return bool(restriction)

    def set_block_all(self, block_all):
        restriction = self._find_restriction_with_type(restrict.BlockAll)
        if block_all:
            if not restriction:
                self.block.add_restriction(restrict.BlockAll())
        elif restriction:
            self.block.remove_restriction(restriction)

    def _find_restriction_with_type(self, rtype):
        for restriction in self.block.get_restrictions():
            if isinstance(restriction, rtype):
                return restriction
        return None


class AddBlockSlotAction(EditAction):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Add')

    def get_extra_payload(self, form):
        adding = form.__parent__
        if adding.block_id is None:
            return {}
        return {
            'block_id': adding.block_id,
            'block_data': adding.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        status = super(AddBlockSlotAction, self).__call__(form)
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        adding = form.__parent__
        controller = form.getContentData().getContent()
        adding.add(controller.block)
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"New slot added."))
        return silvaforms.SUCCESS


VALIDATE_SLOT_ID_RE = re.compile(r'^[a-z0-9A-Z]{3,}$')

def validate_slot_identifier(value, form):
    if value is silvaforms.NO_VALUE:
        return _(u'Identifier required.')
    if not VALIDATE_SLOT_ID_RE.match(value):
        return _(u'Invalid identifier.')
    slots = form.context.slots
    if value in slots:
        current_slot = form.getContentData().getContent().block
        if current_slot != slots[value]:
            return _(u'A slot with that identifier already exists.')
    return None


def _slot_restrictions_block_controller(form):
    slot = form.__parent__.slot
    return BlockSlotController(
        BlockSlot(restrictions=slot.get_restrictions()),
        form.context,
        form.request)

def default_cs_whitelist(form):
    return _slot_restrictions_block_controller(form).get_cs_whitelist()

def default_cs_blacklist(form):
    return _slot_restrictions_block_controller(form).get_cs_blacklist()

def default_content_restriction(form):
    return _slot_restrictions_block_controller(form).get_content_restriction()

def default_block_all(form):
    return _slot_restrictions_block_controller(form).get_block_all()

def require(permission):
    """Helper that verify you have a given permission in the scope of
    a form.
    """

    def available(form):
        manager = getSecurityManager()
        return manager.checkPermission(permission, form.context)

    return available


class AddBlockSlot(silvaforms.RESTPopupForm):
    grok.adapts(IBlockSlot, IPageModelVersion)
    grok.name('add')

    label = _(u'Add a sub-slot')
    description = _(u'You can configure slot options and restrictions here.')

    fields = silvaforms.Fields(IBlockSlotFields)
    fields['tag'].available = require('View Management Screens')
    fields['css_class'].available = require('View Management Screens')
    fields['cs_whitelist'].mode = 'multipickup'
    fields['cs_whitelist'].defaultValue = default_cs_whitelist
    fields['cs_blacklist'].mode = 'multipickup'
    fields['cs_blacklist'].defaultValue = default_cs_blacklist
    fields['content_restriction'].mode = 'combobox'
    fields['content_restriction'].defautValue = default_content_restriction
    fields['block_all'].defaultValue = default_block_all

    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddBlockSlotAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = True
    ignoreRequest = False

    def __init__(self, context, request, configuration, restrictions):
        super(AddBlockSlot, self).__init__(context, request)
        controller = BlockSlotController(BlockSlot(), context, request)
        self.setContentData(controller)
        self.configuration = configuration
        self.restrictions = restrictions

    def update(self):
        super(AddBlockSlot, self).update()
        self.fields['identifier'].validate = validate_slot_identifier


class EditBlockSlotAction(EditAction):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Save changes')

    def get_extra_payload(self, form):
        return {
            'block_id': form.__name__,
            'block_data': form.getContent().render(),
            'block_editable': True}

    def __call__(self, form):
        status = super(EditBlockSlotAction, self).__call__(form)
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        form.send_message(_(u"Slot modified."))
        notify(ObjectModifiedEvent(form.context))
        return silvaforms.SUCCESS


class EditBlockSlot(AddBlockSlot):
    grok.name('edit')

    label = _(u"Edit a sub-slot")
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        EditBlockSlotAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False

    def __init__(self, block, context, request, controller, _):
        super(AddBlockSlot, self).__init__(context, request)
        self.setContentData(controller)
