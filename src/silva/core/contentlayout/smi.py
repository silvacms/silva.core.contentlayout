
import urllib

from five import grok
from zope.interface import alsoProvides, Interface, implementedBy
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.cachedescriptors.property import CachedProperty
from zope import schema
from zeam.form.ztk.interfaces import IFormSourceBinder

from infrae.rest import queryRESTComponent, RESTWithTemplate
from silva.core.interfaces import ISilvaObject
from silva.core.contentlayout.interfaces import IEditionMode, IPage
from silva.core.contentlayout.interfaces import IBlockManager
from silva.core.views import views as silvaviews
from silva.translations import translate as _
from silva.ui.rest import REST
from silva.ui.rest.exceptions import RESTRedirectHandler
from silva.ui.smi import SMIConfiguration
from zeam.form import silva as silvaforms


from zExceptions import BadRequest, NotFound

_marker = object()

class EditPage(silvaviews.Page):
    grok.context(IPage)
    grok.name('edit')
    grok.require('silva.ChangeSilvaContent')

    def update(self):
        alsoProvides(self.request, IEditionMode)

    def render(self):
        template = self.context.get_template()
        render = template(self.context, self.request)
        return render()


class EditorSMIConfiguration(silvaviews.Viewlet):
    grok.viewletmanager(SMIConfiguration)


class EditContentLayoutLayer(RESTWithTemplate):
    """Template for the reference widget.
    """
    grok.context(ISilvaObject)
    grok.name('silva.core.contentlayout.layer')

    def GET(self):
        return self.template.render(self)


class PageAPI(REST):
    grok.context(IPage)
    grok.name('silva.contentlayout')


@grok.provider(IFormSourceBinder)
def block_source(form):
    result = []
    for name, block in form.slot.available_block_types(form.context):
        result.append(SimpleTerm(
                value=urllib.quote(name),
                token=name,
                title=grok.title.bind().get(block)))
    return SimpleVocabulary(result)


class IChooseSchema(Interface):
    category = schema.Choice(
        title=_(u"Block"),
        description=_(u"Select a type of block to include in your document."),
        source=block_source)


class ChooseBlock(silvaforms.RESTPopupForm):
    grok.adapts(PageAPI, IPage)
    grok.name('add')
    grok.require('silva.ChangeSilvaContent')

    label = _(u"Choose a new block to add to the slot")
    fields = silvaforms.Fields(IChooseSchema)
    fields['category'].mode = 'radio'
    actions = silvaforms.Actions(silvaforms.CancelAction())
    slot = None
    slot_id = None

    def publishTraverse(self, request, name):
        if self.slot is None:
            slot_id = urllib.unquote(name)
            # XXX Fix template acess
            template = self.context.get_template()
            if slot_id not in template.slots:
                raise NotFound()
            self.slot = template.slots[slot_id]
            self.slot_id = slot_id
            self.__name__ = '/'.join((self.__name__, name))
            return self

        if self.slot is not None:
            block, restriction = self.slot.get_block_type(name)
            if block is not None:
                adder = queryRESTComponent(
                    (implementedBy(block), self.context),
                    (self.context, request, restriction),
                    name='add',
                    parent=self,
                    id=name)
                if adder is not None:
                    return adder
        return super(ChooseBlock, self).publishTraverse(request, name)

    @silvaforms.action(_('Choose'))
    def choose(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        raise RESTRedirectHandler(data['category'], relative=self, clear=True)


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
            # XXX Fix template acess
            template = self.context.get_template()
            if slot_id not in template.slots:
                raise NotFound('Unknown slot %s' % name)
            self.slot = template.slots[slot_id]
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

    def verify(self, index=_marker):
        if self.slot_id is None:
            raise BadRequest('missing slot identifier')
        if self.block_id is None:
            raise BadRequest('missing block identifier')
        if index is None:
            raise BadRequest('missing index parameter')

    def POST(self, index=None):
        """Move the block to the slot and index
        """
        self.verify(index)
        msg = None
        try:
            self.manager.move(
                self.block_id, self.slot_id, int(index), self.context)
            success = True
        except ValueError as e:
            success = False
            msg = str(e)
        return self.json_response({
                'content': {'success': success, 'message': msg}})


class ValidateBlock(REST):
    grok.adapts(MoveBlock, IPage)
    grok.name('validate')

    def GET(self):
        """Validate that you can move that block to this slot and index.
        """
        move = self.__parent__
        move.verify()
        try:
            success = move.manager.movable(
                move.block_id, move.context, move.slot_id)
        except ValueError:
            success = False
        return self.json_response({'content': {'success': success}})


class RemoveBlock(BlockREST):
    grok.name('delete')

    def GET(self):
        if self.block_id is None:
            raise BadRequest('missing block identifier')
        self.manager.remove(self.block_id, self.context, self.request)
        return self.json_response({'content': {'success': True}})

