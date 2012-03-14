
import uuid

from five import grok
from zope.publisher.interfaces.http import IHTTPRequest
from zope.interface import Interface
from zope.component import getUtility, queryMultiAdapter
from zope.component import getMultiAdapter

from silva.core.contentlayout.blocks import Block
from silva.core.contentlayout.interfaces import IBlockManager
from silva.core.contentlayout.interfaces import IBlockView, IBlockable
from silva.core.contentlayout.interfaces import IReferenceBlock, IPage
from silva.core.interfaces import IDataManager
from silva.core.references.interfaces import IReferenceService
from silva.core.references.reference import Reference
from silva.translations import translate as _
from zeam.form import silva as silvaforms
from zeam.form.silva.interfaces import IRESTCloseOnSuccessAction
from zeam.form.silva.interfaces import IRESTExtraPayloadProvider


class ReferenceBlock(Block):
    grok.implements(IReferenceBlock)
    grok.name('external')
    grok.title(_(u"Site content"))

    def __init__(self):
        self.identifier = unicode(uuid.uuid1())


class BoundReferenceBlock(grok.MultiAdapter):
    grok.adapts(IReferenceBlock, Interface, IHTTPRequest)
    grok.provides(IDataManager)

    def __init__(self, reference, context, request):
        self._name = reference.identifier
        self.context = context
        self.request = request
        self._service = getUtility(IReferenceService)

    @property
    def block(self):
        reference = self._service.get_reference(self.context, name=self._name)
        if reference is not None:
            return reference.target
        return None

    def clear(self):
        self._service.delete_reference(self.context, name=self._name)

    def update(self, parameters):
        reference = self._service.get_reference(
            self.context, name=self._name, add=True)
        if isinstance(parameters, int):
            reference.set_target_id(parameters)
        else:
            reference.set_target(parameters)

    def render(self):
        content = self.block
        if content is None:
            return u'<p>Reference is broken or missing</p>'
        view = queryMultiAdapter((content, self.request), IBlockView)
        if view is None:
            return u'<p>block content is not viewable</p>'
        return view()


class IExternalBlockFields(Interface):
    block = Reference(
        IBlockable,
        title=_(u"Block to include"),
        required=True)


class AddExternalBlockAction(silvaforms.Action):
    grok.implements(IRESTExtraPayloadProvider, IRESTCloseOnSuccessAction)
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
        block = ReferenceBlock()
        self.block_id = manager.new(
            form.request.form['slot_id'],
            block)
        self.block_manager = getMultiAdapter(
            (block, form.context, form.request), IDataManager)
        self.block_manager.update(data['block'])
        form.send_message(_(u"Added new block"))
        return silvaforms.SUCCESS


# Look for add/edit block is non-standard.
class AddExternalBlock(silvaforms.RESTPopupForm):
    grok.adapts(ReferenceBlock, IPage)
    grok.name('add')

    label = _(u"Add an external block ")
    fields = silvaforms.Fields(IExternalBlockFields)
    actions = silvaforms.Actions(
        AddExternalBlockAction(),
        silvaforms.CancelAction())


class EditExternalBlockAction(silvaforms.Action):
    grok.implements(IRESTExtraPayloadProvider, IRESTCloseOnSuccessAction)
    title = _('Edit')

    def get_extra_payload(self, form):
        manager = form.getContent()
        # This is kind of an hack, but the name of the form is the block id.
        return {
            'block_id': form.__name__,
            'block_data': manager.render()}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        manager = form.getContent()
        manager.update(data['block'])
        form.send_message(_(u"Block modified"))
        return silvaforms.SUCCESS


class EditExternalBlock(silvaforms.RESTPopupForm):
    grok.adapts(ReferenceBlock, IPage)
    grok.name('edit')

    label = _(u"Edit an external block ")
    fields = silvaforms.Fields(IExternalBlockFields)
    actions = silvaforms.Actions(
        EditExternalBlockAction(),
        silvaforms.CancelAction())
    ignoreContent = False

    def __init__(self, block, context, request):
        super(EditExternalBlock, self).__init__(context, request)
        self.block = block

    def update(self):
        manager = getMultiAdapter(
            (self.block, self.context, self.request), IDataManager)
        self.setContentData(manager)


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

