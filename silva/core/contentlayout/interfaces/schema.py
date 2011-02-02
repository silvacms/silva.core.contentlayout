from five import grok
from zope.component import getUtility
from zope.interface import Interface
from zope import schema
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm

from silva.translations import translate as _
from silva.core.contentlayout.interfaces.services import IContentLayoutService

@grok.provider(IContextSourceBinder)
def templates_source(context):
    """Source/Vocabulary for all templates
    """
    #XXX this should be converted to get all templates allowed for metatype
    cls = getUtility(IContentLayoutService)
    templates = cls.get_templates()
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