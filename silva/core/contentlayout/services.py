# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

from logging import getLogger
logger = getLogger('silva.core.contentlayout.services')


from five import grok
from persistent.mapping import PersistentMapping

from silva.core.services.base import SilvaService
from zeam.form import silva as silvaforms

from interfaces import IContentLayoutService

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
    
