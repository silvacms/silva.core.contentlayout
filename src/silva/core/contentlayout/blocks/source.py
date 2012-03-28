
from five import grok
from zope import schema
from zope.interface import Interface

from Products.SilvaExternalSources.interfaces import IExternalSourceManager
from Products.SilvaExternalSources.interfaces import SourceError, source_source

from silva.core.contentlayout.blocks import Block
from silva.core.contentlayout.interfaces import IBlockManager, IBlockController
from silva.core.contentlayout.interfaces import IPage, IBlock
from silva.translations import translate as _
from silva.ui.rest.exceptions import RESTRedirectHandler
from zeam.component import getWrapper
from zeam.form import silva as silvaforms


class SourceBlock(Block):
    grok.implements(IBlock)
    grok.name('source')
    grok.title(_(u"Code source"))
    grok.order(5)

    def __init__(self, identifier):
        self.identifier = identifier


def source_controller(block, context, request):
    source = getWrapper(context, IExternalSourceManager)
    return source(request, instance=block.identifier)


grok.global_adapter(
    source_controller,
    (SourceBlock, Interface, Interface),
    IBlockController)


class IAddSourceSchema(Interface):
    source = schema.Choice(
        title=_(u"Select an external source"),
        source=source_source,
        required=True)


class AddSourceBlock(silvaforms.RESTPopupForm):
    grok.adapts(SourceBlock, IPage)
    grok.name('add')

    label = _(u"Add a source block")
    fields = silvaforms.Fields(IAddSourceSchema)
    actions = silvaforms.Actions(silvaforms.CancelAction())

    @silvaforms.action(_('Add'))
    def add(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        raise RESTRedirectHandler(
            'parameters/' + data['source'].getId(), clear=True, relative=self)


class AddSourceBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Add')

    block_id = None

    def get_extra_payload(self, form):
        if self.block_id is None:
            return {}
        try:
            data = form.controller.render()
        except SourceError, error:
            data = error.to_html()
        return {
            'block_id': self.block_id,
            'block_data': data}

    def __call__(self, form):
        status = form.controller.create()
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        manager = IBlockManager(form.context)
        self.block_id = manager.new(
            form.__parent__.__parent__.slot_id,
            SourceBlock(form.controller.getId()))
        form.send_message(_(u"Added new block"))
        return silvaforms.SUCCESS


class AddSourceParameters(silvaforms.RESTPopupForm):
    grok.adapts(AddSourceBlock, IPage)
    grok.name('parameters')

    source = None
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddSourceBlockAction())

    @property
    def label(self):
        if self.controller is not None:
            return _(u"Parameters for new source ${title}",
                     mapping={'title': self.controller.label})
        return _(u"Add a source block")

    @property
    def description(self):
        if self.controller is not None:
            return self.controller.description

    def updateWidgets(self):
        super(AddSourceParameters, self).updateWidgets()
        if self.controller is not None:
            self.fieldWidgets.extend(self.controller.widgets())

    def publishTraverse(self, request, name):
        manager = getWrapper(self.context, IExternalSourceManager)
        try:
            self.controller = manager(self.request, name=name)
        except SourceError:
            parent = super(AddSourceParameters, self)
            return parent.publishTraverse(request, name)
        self.__name__ = '/'.join((self.__name__, name))
        return self


class EditSourceBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Edit')

    def get_extra_payload(self, form):
        if form.controller is None:
            return {}
        return {
            'block_id': form.__name__,
            'block_data': form.controller.render()}

    def __call__(self, form):
        if form.controller is None:
            return silvaforms.FAILURE
        status = form.controller.save()
        if status is silvaforms.SUCCESS:
            form.send_message(_(u"Block modified"))
        return status


class EditSourceBlock(silvaforms.RESTPopupForm):
    grok.adapts(SourceBlock, IPage)
    grok.name('edit')

    label = _(u"Edit an external block ")
    fields = silvaforms.Fields()
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        EditSourceBlockAction())

    def __init__(self, block, context, request):
        super(EditSourceBlock, self).__init__(context, request)
        self.block = block
        manager = getWrapper(context, IExternalSourceManager)
        try:
            self.controller = manager(request, instance=block.identifier)
        except SourceError:
            self.controller = None

    @property
    def label(self):
        if self.controller is not None:
            return _(u"Parameters for existing source ${title}",
                     mapping={'title': self.controller.label})
        return _(u"Edit a source block")

    @property
    def description(self):
        if self.controller is not None:
            return self.controller.description

    def updateWidgets(self):
        super(EditSourceBlock, self).updateWidgets()
        if self.controller is not None:
            self.fieldWidgets.extend(self.controller.widgets())
