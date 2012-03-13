
from five import grok
from zope import schema
from zope.interface import Interface
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from Products.SilvaExternalSources.ExternalSource import availableSources
from Products.SilvaExternalSources.SourceInstance import SourceParameters
from Products.SilvaExternalSources.interfaces import IExternalSource

from silva.ui.rest.exceptions import RESTRedirectHandler
from silva.core.contentlayout.blocks import Block
from silva.core.contentlayout.interfaces import IPage, IBlock
from silva.translations import translate as _
from zeam.form import silva as silvaforms


class SourceBlock(Block, SourceParameters):
    grok.implements(IBlock)
    grok.name('source')
    grok.title(_(u"Code source"))


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
    grok.adapts(SourceBlock, IPage)
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
            'silva.core.contentlayout.add/source/parameters/' +
            data['source'].getId())


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


