
from five import grok
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectModifiedEvent
from zope.traversing.browser import absoluteURL

from Acquisition import aq_base

from Products.Silva.icon import registry as icon_registry
from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaExternalSources.interfaces import IExternalSourceManager
from Products.SilvaExternalSources.interfaces import SourceError
from Products.SilvaExternalSources.interfaces import availableSources

from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from silva.translations import translate as _
from silva.ui.rest.exceptions import RESTRedirectHandler
from zeam.component import Component, getWrapper
from zeam.form import silva as silvaforms

from . import Block
from .contents import ReferenceBlock
from ..interfaces import IPage, IBlock
from ..interfaces import IBlockConfiguration, IBlockConfigurations
from ..interfaces import IBlockManager, IBlockController


class SourceBlock(Block):
    grok.implements(IBlock)
    grok.name('source')
    grok.order(500)
    silvaconf.icon('source.png')

    def __init__(self, identifier):
        self.identifier = identifier


class SourceBlockConfiguration(object):
    grok.implements(IBlockConfiguration)

    def __init__(self, prefix, source, block):
        self.prefix = prefix
        self.identifier = ':'.join((prefix, source.id))
        self.title = source.get_title()
        self.block = block
        self.source = source

    def get_icon(self, view):
        icon = self.source.get_icon()
        if icon is not None:
            return absoluteURL(icon, view.request)
        try:
            icon = icon_registry.get_icon_by_identifier(
                ('silva.core.contentlayout.blocks', self.prefix))
        except ValueError:
            return None
        return '/'.join((view.root_url, icon))

    def is_available(self, view):
        found_source = getattr(view.context, self.source.getId(), None)
        return aq_base(found_source) is aq_base(self.source)


class SourceBlockConfigurations(Component):
    grok.provides(IBlockConfigurations)
    grok.adapts(SourceBlock, Interface)

    def __init__(self, block, context):
        self.block = block
        self.context = context
        self.prefix = grok.name.bind().get(block)

    def get_by_identifier(self, identifier):
        source = getattr(self.context, identifier, None)
        if source is not None and IExternalSource.providedBy(source):
            return SourceBlockConfiguration(self.prefix, source, self.block)
        return None

    def get_all(self):
        for identifier, source in availableSources(self.context):
            yield SourceBlockConfiguration(self.prefix, source, self.block)


def source_controller(block, context, request):
    source = getWrapper(context, IExternalSourceManager)
    return source(request, instance=block.identifier)


grok.global_adapter(
    source_controller,
    (SourceBlock, Interface, Interface),
    IBlockController)


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

    def available(self, form):
        return form.controller is not None

    def __call__(self, form):
        if form.controller is None:
            return silvaforms.FAILURE
        status = form.controller.create()
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        manager = IBlockManager(form.context)
        self.block_id = manager.add(
            form.__parent__.slot_id,
            SourceBlock(form.controller.getId()))
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"Added new source component"))
        return silvaforms.SUCCESS


class AddSourceBlock(silvaforms.RESTPopupForm):
    grok.adapts(SourceBlock, IPage)
    grok.name('add')

    source = None
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddSourceBlockAction())

    def __init__(self, context, request, configuration, restriction):
        super(AddSourceBlock, self).__init__(context, request)
        self.restriction = restriction
        self.configuration = configuration
        manager = getWrapper(self.context, IExternalSourceManager)
        self.controller = manager(self.request, name=configuration.source.id)

    @property
    def label(self):
        if self.controller is not None:
            return _(u"Parameters for new source ${title}",
                     mapping={'title': self.controller.label})
        return _(u"Add a source component")

    @property
    def description(self):
        if self.controller is not None:
            return self.controller.description

    @property
    def formErrors(self):
        if self.controller is not None:
            return self.controller.formErrors
        return []

    def updateWidgets(self):
        super(AddSourceBlock, self).updateWidgets()
        if self.controller is not None:
            self.fieldWidgets.extend(
                self.controller.fieldWidgets(
                    ignoreRequest=False, ignoreContent=True))


class AddSourceBlockLookup(silvaforms.DefaultFormLookup):
    grok.context(AddSourceBlock)

    def fields(self):
        if self.form.controller is not None:
            return self.form.controller.fields
        return silvaforms.Fields()


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

    def available(self, form):
        return form.controller is not None

    def __call__(self, form):
        if form.controller is None:
            return silvaforms.FAILURE
        status = form.controller.save()
        if status is silvaforms.SUCCESS:
            notify(ObjectModifiedEvent(form.context))
            form.send_message(_(u"Source component modified."))
        return status


class EditSourceBlock(silvaforms.RESTPopupForm):
    grok.adapts(SourceBlock, IPage)
    grok.name('edit')

    label = _(u"Edit a source component")
    fields = silvaforms.Fields()
    actions = silvaforms.Actions(silvaforms.CancelAction())

    def __init__(self, block, context, request, controller, restriction):
        super(EditSourceBlock, self).__init__(context, request)
        self.block = block
        self.restriction = restriction
        self.controller = controller

    @property
    def label(self):
        if self.controller is not None:
            return _(u"Parameters for existing source ${title}",
                     mapping={'title': self.controller.label})
        return _(u"Edit a source component")

    @property
    def description(self):
        if self.controller is not None:
            return self.controller.description

    @property
    def formErrors(self):
        if self.controller is not None:
            return self.controller.formErrors
        return []

    def updateWidgets(self):
        super(EditSourceBlock, self).updateWidgets()
        if self.controller is not None:
            self.fieldWidgets.extend(
                self.controller.fieldWidgets(
                    ignoreRequest=False, ignoreContent=False))

    @silvaforms.action(_('Convert'))
    def convert(self):
        raise RESTRedirectHandler('convert', relative=self, clear=True)

    actions += EditSourceBlockAction()


class EditSourceBlockLookup(silvaforms.DefaultFormLookup):
    grok.context(EditSourceBlock)

    def fields(self):
        if self.form.controller is not None:
            return self.form.controller.fields
        return silvaforms.Fields()


class ConvertSourceBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Convert')

    block = None
    block_id = None
    block_controller = None

    def get_extra_payload(self, form):
        return {
            'block_id': self.block_id,
            'block_data': self.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        api = form.__parent__.__parent__
        container = form.context.get_container()
        factory = container.manage_addProduct['SilvaExternalSources']
        factory.manage_addSourceAsset(data['id'], data['title'])
        asset = container._getOb(data['id'])
        editable = asset.get_editable()
        factory = getWrapper(editable, IExternalSourceManager)
        target = factory(form.request, name=api.block_controller.getSourceId())
        target.create()
        api.block_controller.copy(target)
        editable.set_parameters_identifier(target.getId())
        self.block_id = api.manager.replace(api.block_id, ReferenceBlock())
        self.block, self.block_controller = api.manager.get(self.block_id)
        self.block_controller.content = asset
        notify(ObjectModifiedEvent(editable))
        notify(ObjectModifiedEvent(form.context))
        return silvaforms.SUCCESS


class ConvertSourceBlock(silvaforms.RESTPopupForm):
    grok.adapts(EditSourceBlock, IPage)
    grok.name('convert')

    label = _(u"Convert existing source component to asset")
    description = _(u"Create a source asset using current source parameters, "
                    u"and refer to it using a site content component.")
    fields = silvaforms.Fields(ITitledContent)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        ConvertSourceBlockAction())
