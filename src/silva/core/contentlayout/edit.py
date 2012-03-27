
import urllib

from five import grok
from zope.interface import alsoProvides, Interface, implementedBy
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IContextSourceBinder
from zope import schema

from infrae.rest import queryRESTComponent, RESTWithTemplate
from silva.core.interfaces import ISilvaObject, IVersion
from silva.core.contentlayout.blocks.registry import registry
from silva.core.contentlayout.interfaces import IEditionMode, IPage
from silva.core.contentlayout.interfaces import IBlockManager
from silva.core.views import views as silvaviews
from silva.translations import translate as _
from silva.ui.rest import REST, UIREST
from silva.ui.rest.exceptions import RESTRedirectHandler
from silva.ui.smi import SMIConfiguration
from zeam.form import silva as silvaforms

from zExceptions import BadRequest


class EditPage(silvaviews.Page):
    grok.context(IPage)
    grok.name('edit')
    grok.require('silva.ChangeSilvaContent')

    def update(self):
        alsoProvides(self.request, IEditionMode)

    def render(self):
        template = self.context.template(self.context, self.request)
        return template()


class EditorSMIConfiguration(silvaviews.Viewlet):
    grok.viewletmanager(SMIConfiguration)


class EditContentLayoutLayer(RESTWithTemplate):
    """Template for the reference widget.
    """
    grok.context(ISilvaObject)
    grok.name('silva.core.contentlayout.layer')

    def GET(self):
        return self.template.render(self)


@grok.provider(IContextSourceBinder)
def block_source(context):
    result = []
    if IVersion.providedBy(context):
        context = context.get_content()
    for name, block in registry.all(context):
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
    grok.context(IPage)
    grok.name('silva.core.contentlayout.add')
    grok.require('silva.ChangeSilvaContent')

    label = _(u"Choose a new block to add to the slot")
    fields = silvaforms.Fields(IChooseSchema)
    fields['category'].mode = 'radio'
    actions = silvaforms.Actions(silvaforms.CancelAction())
    slot_id = None

    def publishTraverse(self, request, name):
        if self.slot_id is None:
            # XXX Need validation here.
            self.slot_id = urllib.unquote(name)
            self.__name__ = '/'.join((self.__name__, name))
            return self
        block = registry.lookup(urllib.unquote(name))
        if block is not None:
            adder = queryRESTComponent(
                (implementedBy(block), self.context),
                (self.context, request),
                name='add',
                parent=self,
                id=name)
            if adder is not None:
                return adder
        return super(ChooseBlock, self).publishTraverse(request, name)

    @silvaforms.action(_('Next'))
    def next(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        raise RESTRedirectHandler(data['category'], relative=self, clear=True)


class EditBlock(REST):
    grok.context(IPage)
    grok.name('silva.core.contentlayout.edit')
    grok.require('silva.ChangeSilvaContent')

    def publishTraverse(self, request, name):
        manager = IBlockManager(self.context)
        block = manager.get(urllib.unquote(name))
        if block is not None:
            editer = queryRESTComponent(
                (block, self.context),
                (block, self.context, request),
                name='edit',
                parent=self,
                id=name)
            if editer is not None:
                return editer
        return super(EditBlock, self).publishTraverse(request, name)


class BlockUIREST(UIREST):
    """ Traverse to a block on a page.
    """
    grok.baseclass()

    block_id = None

    def publishTraverse(self, request, name):
        manager = IBlockManager(self.context)
        block_id = urllib.unquote(name)
        if manager.get(block_id) is not None:
            self.block_id = block_id
            self.__name__ = '/'.join((self.__name__, name))
            return self
        return super(BlockUIREST, self).publishTraverse(request, name)


class MoveBlock(BlockUIREST):
    grok.context(IPage)
    grok.name('silva.core.contentlayout.move')
    grok.require('silva.ChangeSilvaContent')

    def _validate_parameters(self, slot_id, index):
        if self.block_id is None:
            raise BadRequest("invalid block id")
        if slot_id is None:
            raise BadRequest("invalid slot id")
        if index is None:
            raise BadRequest("invalid index")

    def POST(self, slot_id=None, index=None):
        """Move the block to the slot and index
        """
        self._validate_parameters(slot_id, index)
        manager = IBlockManager(self.context)
        try:
            manager.move(self.block_id,
                         slot_id=slot_id,
                         index=int(index))
            return self.json_response({'content': {'success': True}})
        except ValueError as e:
            raise BadRequest(str(e))

    def GET(self, slot_id=None, index=None):
        """Validate that you can move that block to this slot and index.
        """
        self._validate_parameters(slot_id, index)
        manager = IBlockManager(self.context)
        try:
            can = manager.can_move(self.block_id,
                                   slot_id=slot_id,
                                   index=int(index))
            return self.json_response({'content': {'success': can}})
        except ValueError as e:
            raise BadRequest(str(e))


class RemoveBlock(BlockUIREST):
    grok.context(IPage)
    grok.name('silva.core.contentlayout.delete')
    grok.require('silva.ChangeSilvaContent')

    block_id = None

    def GET(self):
        if self.block_id is None:
            raise BadRequest()
        manager = IBlockManager(self.context)
        manager.remove(self.block_id, self.context, self.request)
        return self.json_response({'content': {'success': True}})

