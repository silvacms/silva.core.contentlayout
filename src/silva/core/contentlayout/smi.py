# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import urllib

from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate
from zope.cachedescriptors.property import Lazy
from zope.component import getUtility, getMultiAdapter
from zope.interface import Interface, implementedBy
from zope.publisher.interfaces.browser import IBrowserRequest

from infrae.rest import queryRESTComponent
from silva.core.views.interfaces import IVirtualSite
from silva.core.views import views as silvaviews
from silva.core.views.httpheaders import ResponseHeaders
from silva.ui.interfaces import IJSView
from silva.ui.rest import REST
from silva.ui.smi import SMIConfiguration

from .interfaces import IPage
from .interfaces import IBoundBlockManager, IBlockGroupLookup
from .slots.slot import Slot, SlotView

from zExceptions import BadRequest, NotFound

_marker = object()


class EditPage(silvaviews.Page):
    grok.context(IPage)
    grok.name('edit')
    grok.require('silva.ChangeSilvaContent')

    def render(self):
        design = self.context.get_design()
        if design is not None:
            render = design(self.context, self.request, [self.context])
            if render is not None:
                return render(edition=True)
        return u'<p>There is no template selected, please select one.</p>'


class EditPageResponseHeaders(ResponseHeaders):
    grok.adapts(IBrowserRequest, EditPage)

    def cachable(self):
        return False


class EditorSMIConfiguration(silvaviews.Viewlet):
    grok.viewletmanager(SMIConfiguration)


class EditorTemplates(object):
    layer = ChameleonPageTemplate(
        filename="smi_templates/layer.cpt")
    components = ChameleonPageTemplate(
        filename="smi_templates/components.cpt")
    missing = ChameleonPageTemplate(
        filename="smi_templates/missing.cpt")


class EditorJSView(grok.MultiAdapter):
    grok.provides(IJSView)
    grok.adapts(Interface, Interface)
    grok.name('content-layout')


    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.screen = None
        self.templates = EditorTemplates()

    def namespace(self):
        return {}

    def default_namespace(self):
        return {"view": self,
                "target_language": self.screen.language}

    def update(self, screen):
        service = getUtility(IBlockGroupLookup)
        self.screen = screen
        self.available = False
        self.block_missing = {}
        self.block_groups = service.lookup_block_groups(self)
        self.root_url = IVirtualSite(self.request).get_root_url()

        design = self.context.get_design()
        if design is None:
            return
        render = design(self.context, self.request, [self.context])
        if render is None:
            return
        render.edition = True
        self.available = True
        slot = Slot()
        blocks = getMultiAdapter(
            (self.context, self.request), IBoundBlockManager)
        slot_missing = set(blocks.manager.get_slot_ids()).difference(
            set(design.slots.keys()))
        for slot_id in slot_missing:
            missing = list(
                blocks.render(SlotView(slot_id, slot, render, self.context)))
            if missing:
                self.block_missing[slot_id] = missing

    def __call__(self, screen, identifier=None):
        self.update(screen)

        return {
            "ifaces": ["content-layout"],
            "available": self.available,
            "missing": self.block_missing,
            "templates": {
                "layer": self.templates.layer.render(self),
                "components": self.templates.components.render(self),
                "missing": self.templates.missing.render(self)},
            "identifier": identifier}


class PageAPI(REST):
    grok.context(IPage)
    grok.name('silva.contentlayout')


class AddBlock(REST):
    grok.adapts(PageAPI, IPage)
    grok.name('add')
    grok.require('silva.ChangeSilvaContent')

    slot = None
    slot_id = None
    block = None
    block_id = None
    block_controller = None

    @property
    def manager(self):
        return getMultiAdapter(
            (self.context, self.request), IBoundBlockManager)

    def add(self, block):
        try:
            index = int(self.request.form.get('index', 0))
        except ValueError:
            index = 0
        self.block_id = self.manager.add(self.slot_id, block, index)
        self.block, self.block_controller = self.manager.get(self.block_id)
        return self.block_controller

    def publishTraverse(self, request, name):
        if self.slot is None:
            slot_id = urllib.unquote(name)
            design = self.context.get_design()
            if slot_id not in design.slots:
                raise NotFound('Unknown slot %s' % slot_id)
            self.slot = design.slots[slot_id]
            self.slot_id = slot_id
            self.__name__ = '/'.join((self.__name__, name))
            return self

        if self.slot is not None:
            service = getUtility(IBlockGroupLookup)
            configuration = service.lookup_block_by_name(self, name)
            if configuration is not None:
                restrictions = self.slot.get_new_restrictions(configuration)
                adder = queryRESTComponent(
                    (implementedBy(configuration.block), self.context),
                    (self.context, request, configuration, restrictions),
                    name='add',
                    parent=self,
                    id=name)
                if adder is not None:
                    return adder
        return super(AddBlock, self).publishTraverse(request, name)


class AddableBlock(REST):
    grok.adapts(PageAPI, IPage)
    grok.name('addable')
    grok.require('silva.ReadSilvaContent')

    slot = None
    slot_id = None
    block_name = None

    def publishTraverse(self, request, name):
        if self.slot is None:
            slot_id = urllib.unquote(name)
            design = self.context.get_design()
            if slot_id not in design.slots:
                raise NotFound('Unknown slot %s' % slot_id)
            self.slot = design.slots[slot_id]
            self.slot_id = slot_id
            self.__name__ = '/'.join((self.__name__, name))
            return self

        if self.slot is not None and self.block_name is None:
            self.block_name = urllib.unquote(name)
            self.__name__ = '/'.join((self.__name__, name))
            return self
        return super(AddableBlock, self).publishTraverse(request, name)

    def GET(self):
        if self.slot_id is None:
            raise BadRequest('Missing slot identifier')
        if self.block_name is None:
            raise BadRequest('Missing block name')

        service = getUtility(IBlockGroupLookup)
        configuration = service.lookup_block_by_name(self, self.block_name)
        if configuration is not None:
            success = self.slot.is_new_block_allowed(
                configuration, self.context)
        else:
            success = False
        return self.json_response({'content': {'success': success}})


class BlockREST(REST):
    """ Traverse to a block on a page.
    """
    grok.baseclass()
    grok.adapts(PageAPI, IPage)
    grok.require('silva.ChangeSilvaContent')

    slot = None
    slot_id = None
    slot_validate = True
    block = None
    block_id = None
    block_controller = None

    @Lazy
    def manager(self):
        return getMultiAdapter(
            (self.context, self.request), IBoundBlockManager)

    def publishTraverse(self, request, name):
        if self.slot_id is None:
            slot_id = urllib.unquote(name)
            if self.slot_validate:
                design = self.context.get_design()
                if slot_id not in design.slots:
                    raise NotFound('Unknown slot %s' % slot_id)
                self.slot = design.slots[slot_id]
            self.slot_id = slot_id
            self.__name__ = '/'.join((self.__name__, name))
            return self

        if self.slot_id is not None and self.block_id is None:
            block_id = urllib.unquote(name)
            block, block_controller = self.manager.get(block_id)
            if block is not None:
                self.block = block
                self.block_id = block_id
                self.block_controller = block_controller
                handler = self.publishBlock(name, request)
                if handler is not None:
                    return handler
        return super(BlockREST, self).publishTraverse(request, name)

    def publishBlock(self, name, request):
        self.__name__ = '/'.join((self.__name__, name))
        return self


class EditBlock(BlockREST):
    grok.name('edit')

    def publishBlock(self, name, request):
        restrictions = self.slot.get_existing_restrictions(self.block)
        return queryRESTComponent(
            (self.block, self.context),
            (self.block, self.context, request, self.block_controller, restrictions),
            name='edit',
            parent=self,
            id=name)


class MoveBlock(BlockREST):
    grok.name('move')

    def POST(self, index=None):
        """Move the block to the slot and index
        """
        if self.slot_id is None:
            raise BadRequest('missing slot identifier')
        if self.block_id is None:
            raise BadRequest('missing block identifier')
        if index is None:
            raise BadRequest('missing index parameter')
        try:
            index = int(index)
        except ValueError:
            raise BadRequest('index is not a valid integer')

        self.manager.move(self.slot_id, self.block_id, index)
        return self.json_response({'content': {'success': True}})


class MovableBlock(BlockREST):
    grok.name('movable')

    def GET(self):
        """Validate that you can move that block to this slot and index.
        """
        if self.slot_id is None:
            raise BadRequest('Missing slot identifier')
        if self.block_id is None:
            raise BadRequest('Missing block identifier')

        success = self.slot.is_existing_block_allowed(
            self.block, self.block_controller, self.context)
        return self.json_response({'content': {'success': success}})


class RemoveBlock(BlockREST):
    grok.name('delete')

    slot_validate = False

    def GET(self):
        if self.block_id is None:
            raise BadRequest('Missing block identifier')
        self.manager.remove(self.block_id)
        return self.json_response({'content': {'success': True}})

