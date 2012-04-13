
from five import grok
from zope import schema
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.vocabulary import SimpleVocabulary

from Products.SilvaExternalSources.interfaces import IExternalSourceManager
from Products.SilvaExternalSources.interfaces import SourceError, source_source
from Products.SilvaExternalSources.interfaces import availableSources

from silva.translations import translate as _
from zeam import component
from zeam.form import silva as silvaforms
from zeam.form.ztk.interfaces import IFormSourceBinder

from Products.SilvaExternalSources.interfaces import IExternalSource

from . import Block
from ..interfaces import IPage, IBlock, IBlockFactories
from ..interfaces import IBlockManager, IBlockController


class SourceBlock(Block):
    grok.implements(IBlock)
    grok.name('source')

    def __init__(self, identifier):
        self.identifier = identifier


class SourceBlockLookup(component.Component):
    component.provides(IBlockFactories)
    grok.adapts(SourceBlock, Interface)

    def __init__(self, factory, context):
        self.factory = factory
        self.context = context

    def get_by_identifier(self, identifier):
        name = grok.name.bind().get(self.factory)
        source = getattr(self.context, identifier, None)
        if source is not None and IExternalSource.providedBy(source):
            return {'name': name + ":" + identifier,
                    'title': source.get_title(),
                    'icon': None,
                    'context': None,
                    'block': self.factory,
                    'source': source}
        return None

    def get_all(self):
        name = grok.name.bind().get(self.factory)
        for identifier, source in availableSources(self.context):
            yield {'name': name + ":" + identifier,
                   'title': source.get_title(),
                   'icon': None,
                   'context': None,
                   'block': self.factory,
                   'source': source}


def source_controller(block, context, request):
    source = component.getWrapper(context, IExternalSourceManager)
    return source(request, instance=block.identifier)


grok.global_adapter(
    source_controller,
    (SourceBlock, Interface, Interface),
    IBlockController)


@grok.provider(IFormSourceBinder)
def form_source_source(form):
    if form.restriction is None:
        return source_source(form.context)

    return SimpleVocabulary([term for term in source_source(form.context)
                             if form.restriction.allow_name(term.token)])


class IAddSourceSchema(Interface):
    source = schema.Choice(
        title=_(u"Select an external source"),
        source=form_source_source,
        required=True)


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
            'block_data': data,
            'block_editable': form.controller.editable()}

    def __call__(self, form):
        status = form.controller.create()
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        manager = IBlockManager(form.context)
        self.block_id = manager.add(
            form.__parent__.slot_id,
            SourceBlock(form.controller.getId()))
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"Added new block"))
        return silvaforms.SUCCESS


class AddSourceParameters(silvaforms.RESTPopupForm):
    grok.adapts(SourceBlock, IPage)
    grok.name('add')

    source = None
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddSourceBlockAction())

    def __init__(self, context, request, identifier=None, restriction=None):
        super(AddSourceParameters, self).__init__(context, request)
        self.restriction = restriction
        manager = component.getWrapper(self.context, IExternalSourceManager)
        self.controller = manager(self.request, name=identifier)

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
            'block_data': form.controller.render(),
            'block_editable': form.controller.editable()}

    def __call__(self, form):
        if form.controller is None:
            return silvaforms.FAILURE
        status = form.controller.save()
        if status is silvaforms.SUCCESS:
            notify(ObjectModifiedEvent(form.context))
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

    def __init__(self, block, context, request, restriction=None):
        super(EditSourceBlock, self).__init__(context, request)
        self.block = block
        self.restriction = restriction
        manager = component.getWrapper(context, IExternalSourceManager)
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
