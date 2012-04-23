
import uuid
from xml.sax.saxutils import quoteattr
from five import grok
from zope.interface import Interface
from zope.publisher.interfaces.http import IHTTPRequest
from zope import schema
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from silva.translations import translate as _
from zeam.form import silva as silvaforms

from .manager import Block, BlockController
from ..interfaces import IPageModelVersion, ISubSlotBlock


class SubSlotBlock(Block):
    grok.implements(ISubSlotBlock)
    grok.name('slot')
    grok.title(_('Sub Slot'))
    grok.context(IPageModelVersion)

    def __init__(self, slot_id, css_class='', restriction=None):
        self.slot_id = slot_id
        self.css_class = css_class
        self.restriction = restriction
        self.identifier = unicode(uuid.uuid1())


class SubSlotBlockController(BlockController):
    """ Controller when used on page model.
    """
    grok.adapts(ISubSlotBlock, IPageModelVersion, IHTTPRequest)

    def render(self):
        return '<div class="subslot">This is a sub-slot</div>'


class SubSlotEditBlockController(BlockController):
    """ Controller when used on the page.
    """
    grok.adapts(ISubSlotBlock, Interface, IHTTPRequest)

    def editable(self):
        return False

    def remove(self):
        return False

    def render(self):
        return ''
        #return ('<div class=%s>This is a sub-slot</div>' %
        #        quoteattr(subslot.css_class))


class ISubSlotBlockFields(Interface):
    css_class = schema.TextLine(
        title=_(u'CSS class(es)'),
        description=_((u'whitespace delimited CSS classes')),
        required=False,
        default=u'')


class AddSubSlotBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Add')

    def get_extra_payload(self, form):
        adding = form.__parent__
        if adding.block_id is None:
            return {}
        return {
            'block_id': adding.block_id,
            'block_data': adding.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        adding = form.__parent__
        adding.add(SubSlotBlock(adding.slot_id, css_class=data['css_class']))
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"New sub-slot block added."))
        return silvaforms.SUCCESS


class AddSubSlotBlock(silvaforms.RESTPopupForm):
    grok.adapts(ISubSlotBlock, IPageModelVersion)
    grok.name('add')

    label = _(u'Add a sub-slot')
    description = _(u'You should be able to configure restrictions here.')
    fields = silvaforms.Fields(ISubSlotBlockFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddSubSlotBlockAction())

    def __init__(self, context, request, configuration, _):
        super(AddSubSlotBlock, self).__init__(context, request)
        self.configuration = configuration


class EditExternalBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Edit')

    def get_extra_payload(self, form):
        return {
            'block_id': form.__name__,
            'block_data': form.getContent().render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        #XXX: fixme
        manager = form.getContentData()
        manager.set('content', data.getWithDefault('content'))
        form.send_message(_(u"Content block modified."))
        notify(ObjectModifiedEvent(form.context))
        return silvaforms.SUCCESS


class EditSubSlotBlock(AddSubSlotBlock):
    grok.name('edit')

    label = _(u"Edit an content block")
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        EditExternalBlockAction())
    ignoreContent = False

    def __init__(self, block, context, request, controller, _):
        super(AddSubSlotBlock, self).__init__(context, request)
        self.block = block
        self.setContentData(controller)
