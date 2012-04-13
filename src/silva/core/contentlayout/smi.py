
import urllib

from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate
from zope.cachedescriptors.property import CachedProperty
from zope.component import getUtility, getMultiAdapter
from zope.interface import alsoProvides, Interface, implementedBy

from infrae.rest import queryRESTComponent
from silva.core.contentlayout.interfaces import IBlockController
from silva.core.contentlayout.interfaces import IBlockManager, IBlockLookup
from silva.core.contentlayout.interfaces import IEditionMode, IPage
from silva.core.views import views as silvaviews
from silva.ui.interfaces import IJSView
from silva.ui.rest import REST
from silva.ui.smi import SMIConfiguration

from zExceptions import BadRequest, NotFound

_marker = object()


class EditPage(silvaviews.Page):
    grok.context(IPage)
    grok.name('edit')
    grok.require('silva.ChangeSilvaContent')

    def update(self):
        alsoProvides(self.request, IEditionMode)

    def render(self):
        design = self.context.get_design()
        if design is not None:
            render = design(self.context, self.request)
            return render()
        return u'<p>There is no design selected, please select one.</p>'


class EditorSMIConfiguration(silvaviews.Viewlet):
    grok.viewletmanager(SMIConfiguration)


class EditorJSView(grok.MultiAdapter):
    grok.provides(IJSView)
    grok.adapts(Interface, Interface)
    grok.name('content-layout')

    layer = ChameleonPageTemplate(filename="smi_templates/layer.cpt")
    components = ChameleonPageTemplate(filename="smi_templates/components.cpt")

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.screen = None

    def namespace(self):
        return {}

    def default_namespace(self):
        return {"view": self,
                "target_language": self.screen.language}

    def __call__(self, screen, identifier=None):
        self.screen = screen
        self.blocks = getUtility(IBlockLookup).lookup_block_groups(self.context)
        return {"ifaces": ["content-layout"],
                "layer": self.layer.render(self),
                "components": self.components.render(self),
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

    def add(self, block):
        try:
            index = int(self.request.form.get('index', 0))
        except ValueError:
            index = 0
        self.block = block
        self.block_id = IBlockManager(self.context).add(
            self.slot_id, block, index)
        self.block_controller = getMultiAdapter(
            (block, self.context, self.request),
            IBlockController)
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
            parts = name.split(":", 1)
            identifier = None
            if len(parts) > 1:
                identifier = parts[1]

            block, restriction = self.slot.get_block_type(name)
            if block is not None:
                adder = queryRESTComponent(
                    (implementedBy(block), self.context),
                    (self.context, request, identifier, restriction),
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

    @CachedProperty
    def manager(self):
        return IBlockManager(self.context)

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
            raise BadRequest('missing slot identifier')
        if self.block_name is None:
            raise BadRequest('missing block name')

        success = False
        block, restriction = self.slot.get_block_type(self.block_name)
        if block is not None:
            success = True
        return self.json_response({'content': {'success': success}})


class BlockREST(REST):
    """ Traverse to a block on a page.
    """
    grok.baseclass()
    grok.adapts(PageAPI, IPage)
    grok.require('silva.ChangeSilvaContent')

    slot = None
    slot_id = None
    block = None
    block_id = None

    @CachedProperty
    def manager(self):
        return IBlockManager(self.context)

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

        if self.slot is not None and self.block is None:
            block_id = urllib.unquote(name)
            block = self.manager.get(block_id)
            if block is not None:
                self.block = block
                self.block_id = block_id
                handler = self.publishBlock(name, request, block)
                if handler is not None:
                    return handler
        return super(BlockREST, self).publishTraverse(request, name)

    def publishBlock(self, name, request, block):
        self.__name__ = '/'.join((self.__name__, name))
        return self


class EditBlock(BlockREST):
    grok.name('edit')

    def publishBlock(self, name, request, block):
        restriction = self.slot.get_block_restriction(block)
        return queryRESTComponent(
            (block, self.context),
            (block, self.context, request, restriction),
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

        message = None
        try:
            self.manager.move(
                self.block_id, self.slot_id, int(index), self.context)
            success = True
        except ValueError as e:
            success = False
            message = str(e)
        return self.json_response({
                'content': {'success': success, 'message': message}})


class MovableBlock(BlockREST):
    grok.name('movable')

    def GET(self):
        """Validate that you can move that block to this slot and index.
        """
        if self.slot_id is None:
            raise BadRequest('missing slot identifier')
        if self.block_id is None:
            raise BadRequest('missing block identifier')

        message = None
        try:
            success = self.manager.movable(
                self.block_id, self.slot_id, self.context)
        except ValueError as error:
            success = False
            message = str(error)
        return self.json_response({
                'content': {'success': success, 'message': message}})


class RemoveBlock(BlockREST):
    grok.name('delete')

    def GET(self):
        if self.block_id is None:
            raise BadRequest('missing block identifier')
        self.manager.remove(self.block_id, self.context, self.request)
        return self.json_response({'content': {'success': True}})

