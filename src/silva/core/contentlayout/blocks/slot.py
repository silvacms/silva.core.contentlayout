
import uuid
from five import grok
from zope.interface import Interface
from zope.publisher.interfaces.http import IHTTPRequest
from zope import schema
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zeam.form.ztk import EditAction

from silva.core.interfaces import IAddableContents
from silva.translations import translate as _
from zeam.form import silva as silvaforms
from Products.SilvaExternalSources.interfaces import availableSources

from .manager import Block, BlockController
from ..interfaces import IPageModelVersion, IBlockSlot
from ..slots.slot import Slot, SlotView
from ..slots import restrictions as restrict


class BlockSlot(Slot, Block):
    grok.implements(IBlockSlot)
    grok.name('slot')
    grok.title(_('Slot'))
    grok.context(IPageModelVersion)

    def __init__(self, tag='div', css_class='', restrictions=None):
        Slot.__init__(self, tag=tag,
                      css_class=css_class,
                      restrictions=restrictions)
        self.identifier = unicode(uuid.uuid1())


@grok.provider(IContextSourceBinder)
def content_type_source(context):
   terms = [SimpleTerm(value=None,
                       token='',
                       title=_(u"-- Choose a content type --"))]
   addables = IAddableContents(
      context.get_root()).get_all_addables()
   # XXX: SHOULD BE INTERFACES
   for addable in addables:
      terms.append(SimpleTerm(value=addable,
                              token=addable,
                              title=addable))
   return SimpleVocabulary(terms)

@grok.provider(IContextSourceBinder)
def code_source_source(context):
    terms = []
    for identifier, _ in availableSources(context.get_root()):
        terms.append(SimpleTerm(value=identifier,
                                title=identifier,
                                token=identifier))
    return SimpleVocabulary(terms)


class IBlockSlotFields(Interface):

    css_class = schema.TextLine(
        title=_(u'CSS class(es)'),
        description=_((u'whitespace delimited CSS classes')),
        required=False,
        default=u'')

    # code source restriction
    cs_whitelist = schema.Set(
        title=_(u"Code source whitelist"),
        value_type=schema.Choice(title=_(u'name'),
                                 source=code_source_source),
        required=False,
        default=set())

    cs_blacklist = schema.Set(
        title=_(u"Code source blacklist"),
        value_type=schema.Choice(title=_(u'name'),
                                 source=code_source_source),
        required=False,
        default=set())

    # content restriction
    content_restriction = schema.Choice(
        title=_(u"Content type"),
        source=content_type_source,
        required=False)

    # block all restriction
    block_all = schema.Bool(
        title=_(u"Block all others"),
        description=_(u'Any block not allowed by restrictions is forbidden'),
        required=False,
        default=False)


class BlockSlotController(BlockController):
    grok.adapts(IBlockSlot, Interface, IHTTPRequest)

    def editable(self):
        return True

    def render(self, view=None):
        if view is not None and not view.final:
            design = view.design
            next_content = design.stack[design.stack.index(view.content) + 1]
            next_view = SlotView(
                self.block.identifier, self.block, design, next_content)
            return next_view()
        return '<div>This is a slot for pages using this model.</div>'

    def get_tag(self):
        return self.block.tag

    def set_tag(self, tag):
        self.block.tag = tag

    def get_css_class(self):
        return self.block.css_class

    def set_css_class(self, css_class):
        self.block.css_class = css_class

    def get_cs_whitelist(self):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            return set()
        return restriction.allowed

    def set_cs_whitelist(self, whitelist):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            self.block._restrictions.insert(
                0, restrict.CodeSourceName(allowed=whitelist))
        else:
            restriction.allowed = whitelist

    def get_cs_blacklist(self):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            return set()
        return restriction.disallowed

    def set_cs_blacklist(self, blacklist):
        restriction = self._find_restriction_with_type(restrict.CodeSourceName)
        if restriction is None:
            self.block._restrictions.insert(
                0, restrict.CodeSourceName(disallowed=blacklist))
        else:
            restriction.disallowed = blacklist

    def get_content_restriction(self):
        restriction = self._find_restriction_with_type(restrict.ContentType)
        if restriction is None:
            return None
        return restriction.content_type

    def set_content_restriction(self, content_type):
        restriction = self._find_restriction_with_type(restrict.ContentType)
        if restriction is None:
            self.block._restrictions.insert(
                0, restrict.ContentType(content_type))
        else:
            restriction.content_type = content_type

    def get_block_all(self):
        restriction = self._find_restriction_with_type(restrict.BlockAll)
        return bool(restriction)

    def set_block_all(self, block_all):
        restriction = self._find_restriction_with_type(restrict.BlockAll)
        if block_all:
            if not restriction:
                self.block._restrictions.append(restrict.BlockAll())
        elif restriction:
            self.block._restrictions.remove(restriction)

    def _find_restriction_with_type(self, rtype):
        for restriction in self.block._restrictions:
            if isinstance(restriction, rtype):
                return restriction
        return None


class AddBlockSlotAction(EditAction):
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
        status = super(AddBlockSlotAction, self).__call__(form)
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        adding = form.__parent__
        controller = form.getContentData().getContent()
        adding.add(controller.block)
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
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = True
    ignoreRequest = False

    def __init__(self, context, request, configuration, restriction):
        super(AddBlockSlot, self).__init__(context, request)
        controller = BlockSlotController(BlockSlot(), context, request)
        self.setContentData(controller)
        self.configuration = configuration
        self.restriction = restriction


class EditBlockSlotAction(EditAction):
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
        status = super(EditBlockSlotAction, self).__call__(form)
        if status is silvaforms.FAILURE:
            return silvaforms.FAILURE
        form.send_message(_(u"Slot modified."))
        notify(ObjectModifiedEvent(form.context))
        return silvaforms.SUCCESS


class EditBlockSlot(AddBlockSlot):
    grok.name('edit')

    label = _(u"Edit an content block")
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        EditBlockSlotAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False

    def __init__(self, block, context, request, controller, _):
        super(AddBlockSlot, self).__init__(context, request)
        self.setContentData(controller)
