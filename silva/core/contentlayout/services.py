# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

from logging import getLogger
logger = getLogger('silva.core.contentlayout.services')

from five import grok
from zope.component import getUtility, getUtilitiesFor
from persistent.mapping import PersistentMapping

from silva.core.services.base import SilvaService
from silva.translations import translate as _
from zeam.form import silva as silvaforms

from interfaces import IContentLayoutService
from templates.interfaces import ITemplate

class ContentLayoutService(SilvaService):
    meta_type = 'Silva Content Layout Service'
    grok.implements(IContentLayoutService)
    default_service_identifier = 'service_contentlayout'

    manage_options = (
        {'label':'Mappings',
         'action':'manage_main'},
        {'label':'Templates',
         'action':'manage_templates'}
        ) + SilvaService.manage_options

    def __init__(self, id):
        super(ContentLayoutService, self).__init__(id)
        self._content_mapping = PersistentMapping()
        
    def getTemplates(self):
        """return all registered ITemplates"""
        return getUtilitiesFor(ITemplate)
    
    def getSortedTemplates(self):
        """returns the list of templates, sorted by their priority"""
        templates = [ (t[1].priority, t[1].name, t[0], t)  for \
                      t in self.getTemplates() ]
        return [ t[-1] for t in sorted(templates) ]
    
    def getTemplateByName(self, name):
        """returns the ITemplate with the given name"""
        return getUtility(ITemplate, name)


    
class ContentLayoutMappings(silvaforms.ZMIForm):
    name = 'manage_main'
    grok.name(name)
    grok.context(IContentLayoutService)
    
    label = u"Layout Template Mappings for Silva Content Types"
    description = (u"Each Content Type can have a default template and a list "
                   u"of allowed templates. The default template will be "
                   u"selected on the add screen.  The list of allowed "
                   u"templates will be displayed on the add screen and in "
                   u"the content layout editor's info panel "
                   u"(allowing authors to switch between templates)")
    
    def update(self):
        from silva.core.contentlayout import contentlayout as cl
        from silva.core.contentlayout.interfaces import IContentLayoutService
        from interfaces import *
        from zope.component import getUtility
        super(ContentLayoutMappings, self).update()
        self.templates = self.context.getTemplates()

        
