
import uuid

from five import grok
from zope.publisher.interfaces.http import IHTTPRequest
from zope.interface import Interface
from zope.component import getUtility, queryMultiAdapter
from zope.component import getMultiAdapter

from silva.core.contentlayout.blocks import Block, BlockController
from silva.core.contentlayout.interfaces import IBlockManager, IBlockController
from silva.core.contentlayout.interfaces import IBlockView, IBlockable
from silva.core.contentlayout.interfaces import IReferenceBlock, IPage
from silva.core.contentlayout.interfaces import IContentSlotRestriction
from silva.core.references.interfaces import IReferenceService
from silva.core.references.reference import Reference
from silva.translations import translate as _
from zeam.form import silva as silvaforms


class ReferenceBlock(Block):
    grok.implements(IReferenceBlock)
    grok.name('site-content')
    grok.title(_(u"Site content"))
    grok.order(15)

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

    def render(self):
        content = self.content
        if content is None:
            return u'<p>Reference is broken or missing</p>'
        view = queryMultiAdapter((content, self.request), IBlockView)
        if view is None:
            return u'<p>block content is not viewable</p>'
        return view()


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

    block_id = None
    block_controller = None

    def get_extra_payload(self, form):
        if self.block_id is None:
            return {}
        return {
            'block_id': self.block_id,
            'block_data': self.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        block = ReferenceBlock()
        self.block_id = IBlockManager(form.context).new(
            form.__parent__.slot_id,
            block)
        self.block_controller = getMultiAdapter(
            (block, form.context, form.request), IBlockController)
        self.block_controller.content = data['content']
        form.send_message(_(u"New content block added."))
        return silvaforms.SUCCESS


# Look for add/edit block is non-standard.
class AddExternalBlock(silvaforms.RESTPopupForm):
    grok.adapts(ReferenceBlock, IPage)
    grok.name('add')

    label = _(u"Add an content block ")
    baseFields = silvaforms.Fields(IExternalBlockFields)
    actions = silvaforms.Actions(
        AddExternalBlockAction(),
        silvaforms.CancelAction())

    def __init__(self, context, request, restriction=None):
        super(AddExternalBlock, self).__init__(context, request)
        self.restriction = restriction

    def update(self):
        field = self.baseFields['content'].clone()
        if IContentSlotRestriction.providedBy(self.restriction):
            field.schema = self.restriction.schema
        self.fields = silvaforms.Fields(field)


class EditExternalBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Edit')

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
        form.send_message(_(u"Content block modified."))
        return silvaforms.SUCCESS


class EditExternalBlock(AddExternalBlock):
    grok.name('edit')

    label = _(u"Edit an content block")
    actions = silvaforms.Actions(
        EditExternalBlockAction(),
        silvaforms.CancelAction())
    ignoreContent = False

    def __init__(self, block, context, request, restriction=None):
        super(EditExternalBlock, self).__init__(context, request, restriction)
        self.block = block

    def update(self):
        self.setContentData(getMultiAdapter(
                (self.block, self.context, self.request), IBlockController))
        super(EditExternalBlock, self).update()


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

