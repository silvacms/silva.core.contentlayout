# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import uuid

from Acquisition import aq_base

from five import grok
from zope.component import getUtility, queryMultiAdapter
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectModifiedEvent
from zope.publisher.interfaces.http import IHTTPRequest

from silva.core import conf as silvaconf
from silva.core.interfaces.adapters import IIndexEntries
from silva.core.references.interfaces import IReferenceService
from silva.core.references.reference import Reference
from silva.translations import translate as _
from zeam.form import silva as silvaforms

from silva.core.contentlayout.blocks import Block, BlockController
from silva.core.contentlayout.interfaces import IBlockView, IBlockable
from silva.core.contentlayout.interfaces import IContentSlotRestriction
from silva.core.contentlayout.interfaces import IReferenceBlock, IPage


class ReferenceBlock(Block):
    grok.implements(IReferenceBlock)
    grok.name('site-content')
    grok.title(_(u"Site content"))
    grok.order(10)
    silvaconf.icon('contents.png')

    def __init__(self):
        self.identifier = unicode(uuid.uuid1())


class ReferenceBlockController(BlockController):
    grok.adapts(IReferenceBlock, Interface, IHTTPRequest)

    def __init__(self, block, context, request):
        super(ReferenceBlockController, self).__init__(block, context, request)
        self._name = block.identifier
        self._service = getUtility(IReferenceService)

    def editable(self):
        return True

    @apply
    def content():

        def getter(self):
            reference = self._service.get_reference(
                self.context, name=self._name)
            if reference is not None:
                return reference.target
            return None

        def setter(self, value):
            reference = self._service.get_reference(
                self.context, name=self._name, add=True)
            if isinstance(value, int):
                reference.set_target_id(value)
            else:
                reference.set_target(value)

        return property(getter, setter)

    def remove(self):
        self._service.delete_reference(self.context, name=self._name)

    def indexes(self):
        entries = IIndexEntries(self.content, None)
        if entries is not None:
            return entries.get_entries()
        return []

    def fulltext(self):
        content = self.content
        if hasattr(aq_base(content), 'fulltext'):
            return content.fulltext()
        return []

    def render(self, view=None):
        content = self.content
        if content is None:
            return _(u'Content reference is broken or missing.')
        block_view = queryMultiAdapter((content, self.request), IBlockView)
        if block_view is None:
            return _(u'Content is not viewable.')
        return block_view()


class IExternalBlockFields(Interface):
    content = Reference(
        IBlockable,
        title=_(u"Content to include"),
        required=True)


class AddExternalBlockAction(silvaforms.Action):
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
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        adding = form.__parent__
        adding.add(ReferenceBlock()).content = data['content']
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"New site content component added."))
        return silvaforms.SUCCESS


# Look for add/edit block is non-standard.
class AddExternalBlock(silvaforms.RESTPopupForm):
    grok.adapts(ReferenceBlock, IPage)
    grok.name('add')

    label = _(u"Add a site content component")
    baseFields = silvaforms.Fields(IExternalBlockFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddExternalBlockAction())

    def __init__(self, context, request, configuration, restrictions):
        super(AddExternalBlock, self).__init__(context, request)
        self.restrictions = restrictions
        self.configuration = configuration

    def update(self):
        field = self.baseFields['content'].clone()
        for restriction in self.restrictions:
            if IContentSlotRestriction.providedBy(restriction):
                field.schema = restriction.schema
        self.fields = silvaforms.Fields(field)


class EditExternalBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Save changes')

    def get_extra_payload(self, form):
        # This is kind of an hack, but the name of the form is the block id.
        return {
            'block_id': form.__name__,
            'block_data': form.getContent().render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        manager = form.getContentData()
        manager.set('content', data.getWithDefault('content'))
        form.send_message(_(u"Site content component modified."))
        notify(ObjectModifiedEvent(form.context))
        return silvaforms.SUCCESS


class EditExternalBlock(AddExternalBlock):
    grok.name('edit')

    label = _(u"Edit a site content component")
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        EditExternalBlockAction())
    ignoreContent = False

    def __init__(self, block, context, request, controller, restrictions):
        super(AddExternalBlock, self).__init__(context, request)
        self.restrictions = restrictions
        self.block = block
        self.setContentData(controller)


class BlockView(object):
    """A view on a block for an external content.
    """
    grok.implements(IBlockView)
    grok.baseclass()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def default_namespace(self):
        namespace = {}
        namespace['view'] = self
        namespace['context'] = self.context
        namespace['request'] = self.request
        return namespace

    def namespace(self):
        return {}

    def update(self):
        pass

    def render(self):
        return self.template.render(self)

    render.base_method = True

    def __call__(self):
        self.update()
        return self.render()

