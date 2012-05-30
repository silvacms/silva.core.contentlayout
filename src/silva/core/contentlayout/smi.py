
import urllib

from five import grok
from grokcore.chameleon.components import ChameleonPageTemplate
from zope.cachedescriptors.property import CachedProperty
from zope.component import getUtility, getMultiAdapter
from zope.interface import Interface, implementedBy

from infrae.rest import queryRESTComponent
from silva.core.views.interfaces import IVirtualSite
from silva.core.views import views as silvaviews
from silva.ui.interfaces import IJSView
from silva.ui.rest import REST
from silva.ui.smi import SMIConfiguration

from .interfaces import IPage
from .interfaces import IBoundBlockManager, IBlockGroupLookup

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
        service = getUtility(IBlockGroupLookup)
        self.root_url = IVirtualSite(self.request).get_root_url()
        self.screen = screen
        self.blocks = service.lookup_block_groups(self)
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
                restriction = self.slot.get_new_restriction(configuration)
                adder = queryRESTComponent(
                    (implementedBy(configuration.block), self.context),
                    (self.context, request, configuration, restriction),
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
            raise BadRequest('missing slot identifier')
        if self.block_name is None:
            raise BadRequest('missing block name')

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
    block = None
    block_id = None
    block_controller = None

    @CachedProperty
    def manager(self):
        return getMultiAdapter(
            (self.context, self.request), IBoundBlockManager)

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
        restriction = self.slot.get_existing_restriction(self.block)
        return queryRESTComponent(
            (self.block, self.context),
            (self.block, self.context, request, self.block_controller, restriction),
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
            raise BadRequest('missing slot identifier')
        if self.block_id is None:
            raise BadRequest('missing block identifier')

        success = self.slot.is_existing_block_allowed(
            self.block, self.block_controller, self.context)
        return self.json_response({'content': {'success': success}})


class RemoveBlock(BlockREST):
    grok.name('delete')

    def GET(self):
        if self.block_id is None:
            raise BadRequest('missing block identifier')
        self.manager.remove(self.block_id)
        return self.json_response({'content': {'success': True}})

