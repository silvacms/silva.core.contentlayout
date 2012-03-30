
import uuid

from five import grok
from zope.publisher.interfaces.http import IHTTPRequest
from zope.interface import Interface
from zope.component import getMultiAdapter
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from silva.core.contentlayout.blocks.contents import ReferenceBlock
from silva.core.conf import schema as silvaschema
from silva.core.conf.interfaces import ITitledContent
from silva.core.contentlayout.blocks import Block, BlockController
from silva.core.contentlayout.interfaces import IBlockManager, IBlockController
from silva.core.contentlayout.interfaces import ITextBlock, IPage
from silva.core.editor.text import Text
from silva.core.editor.transform.interfaces import IInputEditorFilter
from silva.core.editor.transform.interfaces import ISaveEditorFilter
from silva.translations import translate as _
from silva.ui.rest.exceptions import RESTRedirectHandler
from zeam.form import silva as silvaforms


class TextBlock(Text, Block):
    grok.implements(ITextBlock)
    grok.name('text')
    grok.title(_(u"Rich text"))
    grok.order(1)

    def __init__(self):
        self.identifier = u'text block %s' % uuid.uuid1()
        super(TextBlock, self).__init__(self.identifier)


class TextBlockController(BlockController):
    grok.adapts(ITextBlock, Interface, IHTTPRequest)

    def editable(self):
        return True

    @apply
    def text():

        def getter(self):
            return self.block.render(
                self.context,
                self.request,
                type=IInputEditorFilter)

        def setter(self, value):
            self.block.save(
                self.context,
                self.request,
                value,
                type=ISaveEditorFilter)

        return property(getter, setter)

    def render(self):
        return self.block.render(self.context, self.request)


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
            'block_data': self.block_manager.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        block = TextBlock()
        self.block_id = IBlockManager(form.context).new(
            form.__parent__.slot_id,
            block)
        self.block_manager = getMultiAdapter(
            (block, form.context, form.request), IBlockController)
        self.block_manager.text = data['text']
        form.send_message(_(u"New text block added."))
        return silvaforms.SUCCESS


class AddTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(TextBlock, IPage)
    grok.name('add')

    label = _(u"Add a text block ")
    fields = silvaforms.Fields(ITextBlockFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddTextBlockAction())

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
            'block_data': self.block_manager.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        manager = form.getContentData()
        manager.set('text', data.getWithDefault('text'))
        form.send_message(_(u"Text block modified."))
        self.block_manager = getMultiAdapter(
            (form.block, form.context, form.request), IBlockController)
        return silvaforms.SUCCESS


class EditTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(ITextBlock, IPage)
    grok.name('edit')

    label = _(u"Edit a text block")
    fields = silvaforms.Fields(ITextBlockFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction())
    ignoreContent = False

    def __init__(self, block, context, request, restriction=None):
        super(EditTextBlock, self).__init__(context, request)
        self.block = block
        self.restriction = restriction
        self.setContentData(
            getMultiAdapter((block, context, request), IBlockController))

    @silvaforms.action(_('Convert'))
    def convert(self):
        raise RESTRedirectHandler('convert', relative=self, clear=True)

    actions += EditTextBlockAction()



class ConvertTextBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Convert')

    def get_extra_payload(self, form):
        return {
            'block_id': form.__name__,
            'block_data': self.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        current = getMultiAdapter(
            (form.__parent__.block, form.context, form.request),
            IBlockController)
        container = form.context.get_container()
        factory = container.manage_addProduct['silva.app.document']
        factory.manage_addDocument(data['id'], data['title'])
        document = container._getOb(data['id'])
        version = document.get_editable()
        version.body.save(
            version,
            form.request,
            current.text,
            type=ISaveEditorFilter)
        notify(ObjectModifiedEvent(version))
        new_block = ReferenceBlock()
        self.block_controller = getMultiAdapter(
            (new_block, form.context, form.request), IBlockController)
        self.block_controller.content = document
        IBlockManager(form.context).replace(
            form.__parent__.__parent__.block_id, new_block,
            form.context, form.request)
        return silvaforms.SUCCESS


class ConvertTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(EditTextBlock, IPage)
    grok.name('convert')

    label = _(u"Convert block to document")
    fields = silvaforms.Fields(ITitledContent)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        ConvertTextBlockAction())

