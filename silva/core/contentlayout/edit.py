
import urllib

from five import grok
from zope.interface import alsoProvides, Interface, implementedBy
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IContextSourceBinder
from zope import schema

from infrae.rest import queryRESTComponent

from silva.core.contentlayout.blocks.registry import registry
from silva.core.contentlayout.interfaces import IEditionMode, IPage
from silva.core.contentlayout.interfaces import IBlockManager
from silva.core.views import views as silvaviews
from silva.translations import translate as _
from silva.ui.rest import REST
from silva.ui.rest.exceptions import RESTRedirectHandler
from silva.ui.smi import SMIConfiguration
from zeam.form import silva as silvaforms


class EditPage(silvaviews.Page):
    grok.context(IPage)
    grok.name('edit')

    def update(self):
        alsoProvides(self.request, IEditionMode)

    def render(self):
        template = self.context.template(self.context, self.request)
        return template()


class EditorSMIConfiguration(silvaviews.Viewlet):
    grok.viewletmanager(SMIConfiguration)



@grok.provider(IContextSourceBinder)
def block_source(context):
    result = []
    for name, block in registry.all():
        result.append(SimpleTerm(
                value='silva.core.contentlayout.add/' + urllib.quote(name),
                token=name,
                title=grok.title.bind().get(block)))
    return SimpleVocabulary(result)


class IAddSchema(Interface):
    category = schema.Choice(
        title=_(u"Block"),
        description=_(u"Select a type of block to include in your document."),
        source=block_source)


class AddBlock(silvaforms.RESTPopupForm):
    grok.context(IPage)
    grok.name('silva.core.contentlayout.add')

    label = _(u"Add a new block to the slot")
    fields = silvaforms.Fields(IAddSchema)
    fields['category'].mode = 'radio'
    actions = silvaforms.Actions(silvaforms.CancelAction())

    def publishTraverse(self, request, name):
        block = registry.lookup(urllib.unquote(name))
        if block is not None:
            adder = queryRESTComponent(
                (implementedBy(block), self.context),
                (self.context, request),
                name='add',
                parent=self,
                id=name)
            if adder is not None:
                return adder
        return super(AddBlock, self).publishTraverse(request, name)

    @silvaforms.action(_('Next'))
    def add(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        raise RESTRedirectHandler(data['category'])


class EditBlock(REST):
    grok.context(IPage)
    grok.name('silva.core.contentlayout.edit')

    def publishTraverse(self, request, name):
        manager = IBlockManager(self.context)
        block = manager.get(urllib.unquote(name))
        if block is not None:
            editer = queryRESTComponent(
                (block, self.context),
                (block, self.context, request),
                name='edit',
                parent=self,
                id=name)
            if editer is not None:
                return editer
        return super(EditBlock, self).publishTraverse(request, name)


