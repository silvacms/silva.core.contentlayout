from five import grok
from zope.publisher.interfaces.http import IHTTPRequest
from zope.interface import Interface
from zope.component import getMultiAdapter

from silva.core.conf import schema as silvaschema
from silva.core.contentlayout.blocks import Block, BlockController
from silva.core.contentlayout.interfaces import IBlockManager, IBlockController
from silva.core.contentlayout.interfaces import ITextBlock, IPage
from silva.translations import translate as _
from zeam.form import silva as silvaforms


class TextBlock(Block):
    grok.implements(ITextBlock)
    grok.name('text')
    grok.title(_(u"Rich text"))
    grok.order(1)

    def __init__(self, text=u""):
        self.text = text


class TextBlockController(BlockController):
    grok.adapts(ITextBlock, Interface, IHTTPRequest)

    def editable(self):
        return True

    def render(self):
        return self.block.text


class ITextBlockFields(Interface):
    text = silvaschema.HTMLText(
        title=_(u"Text"),
        required=True)


class AddTextBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Add')

    block_id = None
    block_manager = None

    def get_extra_payload(self, form):
        if self.block_id is None:
            return {}
        return {
            'block_id': self.block_id,
            'block_data': self.block_manager.render()}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        manager = IBlockManager(form.context)
        block = TextBlock(data['text'])
        self.block_id = manager.new(
            form.__parent__.slot_id,
            block)
        self.block_manager = getMultiAdapter(
            (block, form.context, form.request), IBlockController)
        form.send_message(_(u"New text block added."))
        return silvaforms.SUCCESS


class AddTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(TextBlock, IPage)
    grok.name('add')

    label = _(u"Add a text block ")
    fields = silvaforms.Fields(ITextBlockFields)
    actions = silvaforms.Actions(
        AddTextBlockAction(),
        silvaforms.CancelAction())

    def __init__(self, context, request, restriction=None):
        super(AddTextBlock, self).__init__(context, request)
        self.restriction = restriction


class EditTextBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Edit')

    def get_extra_payload(self, form):
        return {
            'block_id': form.__name__,
            'block_data': self.block_manager.render()}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        form.block.text = data['text']
        form.send_message(_(u"Text block modified."))
        self.block_manager = getMultiAdapter(
            (form.block, form.context, form.request), IBlockController)
        return silvaforms.SUCCESS


class EditTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(ITextBlock, IPage)
    grok.name('edit')

    label = _(u"Edit a text block ")
    fields = silvaforms.Fields(ITextBlockFields)
    actions = silvaforms.Actions(
        EditTextBlockAction(),
        silvaforms.CancelAction())
    ignoreContent = False

    def __init__(self, block, context, request, restriction=None):
        super(EditTextBlock, self).__init__(context, request)
        self.block = block
        self.setContentData(block)
        self.restriction = restriction
