
from five import grok
from zope.interface import alsoProvides, Interface
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.schema.interfaces import IContextSourceBinder
from zope import schema

from Products.SilvaExternalSources.ExternalSource import availableSources
from Products.SilvaExternalSources.interfaces import IExternalSource

from silva.core.contentlayout.interfaces import IEditionMode, IPage, IPageBlock
from silva.core.references.reference import Reference
from silva.core.views import views as silvaviews
from silva.translations import translate as _
from silva.ui.rest.exceptions import RESTRedirectHandler
from silva.ui.smi import SMIConfiguration
from zeam.form import silva as silvaforms


class EditPage(silvaviews.Page):
    grok.context(IPage)
    grok.name('edit')

    def update(self):
        alsoProvides(self.request, IEditionMode)

    def render(self):
        content = self.context.get_editable()
        template = content.template(content, self.request)
        return template()


class EditorSMIConfiguration(silvaviews.Viewlet):
    grok.viewletmanager(SMIConfiguration)



block_source = SimpleVocabulary([
        SimpleTerm(
            value='silva.core.contentlayout.add/source',
            token='source',
            title=_(u"Code source")),
        SimpleTerm(
            value='silva.core.contentlayout.add/external',
            token='external',
            title=_(u"Site content"))])


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

    @silvaforms.action(_('Next'))
    def add(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        raise RESTRedirectHandler(data['category'])


@grok.provider(IContextSourceBinder)
def source_source(context):

    def make_term(identifier, source):
        return SimpleTerm(value=source,
                          token=identifier,
                          title=unicode(source.title))

    return SimpleVocabulary([make_term(*t) for t in availableSources(context)])


class IAddSourceSchema(Interface):
    source = schema.Choice(
        title=_(u"Select a source"),
        source=source_source,
        required=True)


class AddSourceBlock(silvaforms.RESTPopupForm):
    grok.adapts(AddBlock, IPage)
    grok.name('source')

    label = _(u"Add a source in a new block")
    fields = silvaforms.Fields(IAddSourceSchema)
    actions = silvaforms.Actions(silvaforms.CancelAction())

    @silvaforms.action(_('Add'))
    def add(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        raise RESTRedirectHandler(
            'silva.core.contentlayout.add/source/parameters/' + data['source'].getId())


class AddSourceParameters(silvaforms.RESTPopupForm):
    grok.adapts(AddSourceBlock, IPage)
    grok.name('parameters')

    source = None
    description = u'Dead end.'
    actions = silvaforms.Actions(silvaforms.CancelAction())

    @property
    def label(self):
        return _(u"Parameters for source ${title} in a new block",
                 mapping={'title': self.source.title})

    def publishTraverse(self, request, name):
        candidate = getattr(self.context, name, None)
        if candidate is not None:
            if IExternalSource.providedBy(candidate):
                self.source = candidate
                self.__name__ = '/'.join((self.__name__, name))
                return self
        return super(AddSourceParameters, self).publishTraverse(request, name)


class IAddExternalSchema(Interface):
    block = Reference(
        IPageBlock,
        title=_(u"Block to include"),
        required=True)


class AddExternalBlock(silvaforms.RESTPopupForm):
    grok.adapts(AddBlock, IPage)
    grok.name('external')

    label = _(u"Add an external block ")
    fields = silvaforms.Fields(IAddExternalSchema)
    actions = silvaforms.Actions(silvaforms.CancelAction())

    @silvaforms.action(_('Add'))
    def add(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        return silvaforms.SUCCESS
