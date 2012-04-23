
import uuid
from five import grok
from zope.interface import Interface
from zope.publisher.interfaces.http import IHTTPRequest
from zope import schema
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from silva.core import conf as silvaconf
from silva.translations import translate as _
from zeam.form import silva as silvaforms

from .manager import Block, BlockController
from ..interfaces import IPageModelVersion, IBlockSlot
from ..slots.slot import SlotView


class BlockSlot(Block):
    grok.implements(IBlockSlot)
    grok.name('slot')
    grok.title(_('Slot'))
    grok.context(IPageModelVersion)
    silvaconf.icon('slot.png')

    def __init__(self, css_class='', restriction=None):
        self.tag = 'div'
        self.css_class = css_class
        self.restriction = restriction
        self.identifier = unicode(uuid.uuid1())

    def is_new_block_allowed(self, configuration, context):
        return True

    def is_existing_block_allowed(self, block, controller, context):
        return True

    def get_new_restriction(self, configuration):
        return None

    def get_existing_restriction(self, block):
        return None


class SlotBlockEditController(BlockController):
    """ Controller when used on the page.
    """
    grok.adapts(IBlockSlot, Interface, IHTTPRequest)

    def editable(self):
        return False

    def remove(self):
        return False

    def render(self, view=None):
        if view is not None and not view.final:
            design = view.design
            next_content = design.stack[design.stack.index(view.content) + 1]
            next_view = SlotView(
                self.block.identifier, self.block, design, next_content)
            return next_view()
        return '<div>This is a slot for pages using this model.</div>'


class IBlockSlotFields(Interface):
    css_class = schema.TextLine(
        title=_(u'CSS class(es)'),
        description=_((u'whitespace delimited CSS classes')),
        required=False,
        default=u'')


class AddBlockSlotAction(silvaforms.Action):
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
            'block_editable': False}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        adding = form.__parent__
        adding.add(BlockSlot(css_class=data['css_class']))
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"New slot added."))
        return silvaforms.SUCCESS


class AddBlockSlot(silvaforms.RESTPopupForm):
    grok.adapts(IBlockSlot, IPageModelVersion)
    grok.name('add')

    label = _(u'Add a sub-slot')
    description = _(u'You should be able to configure restrictions here.')
    fields = silvaforms.Fields(IBlockSlotFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddBlockSlotAction())

    def __init__(self, context, request, configuration, restriction):
        super(AddBlockSlot, self).__init__(context, request)
        self.configuration = configuration
        self.restriction = restriction
