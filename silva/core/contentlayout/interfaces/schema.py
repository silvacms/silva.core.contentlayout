from five import grok
from zope.component import getUtility
from zope.interface import Interface
from zope import schema
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from silva.translations import translate as _
from silva.core.interfaces import (IContentLayout, IVersionedContentLayout,
                                   IContainer)
from silva.core.contentlayout.interfaces.services import IContentLayoutService

@grok.provider(IContextSourceBinder)
def templates_source(context):
    """Source/Vocabulary for all templates
    """
    cls = getUtility(IContentLayoutService)
    templates = cls.get_templates()
    if IContentLayout.providedBy(context) or \
       IVersionedContentLayout.providedBy(context):
        templates = cls.get_allowed_templates(context.meta_type)
    elif IContainer.providedBy(context):
        # check if this is an AddingView.  If so, the last item in steps
        # will be the meta_type to filter by
        r = getattr(context, 'REQUEST', None)
        if r and len(r.steps) > 2 and r.steps[-2] == '+':
            meta_type = r.steps[-1]
            templates = cls.get_allowed_templates(meta_type)
    contents = []
    for t in templates:
        contents.append(SimpleTerm(
            value=t[0],
            token=t[0],
            title=t[1].name))
    return SimpleVocabulary(contents)

class ITemplateSchema(Interface):
    """Schema for the Silva Page add screen
    """
    template = schema.Choice(
            title=_(u"Content Layout Template"),
            description=_(u"The content layout template to use"),
            source=templates_source,
    )

__all__ = ['ITemplateSchema']