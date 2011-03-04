# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

import sys, os
from logging import getLogger
logger = getLogger('silva.core.contentlayout.services')

from five import grok
from zope.component import getUtility, getUtilitiesFor
from persistent.mapping import PersistentMapping

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.ImageFile import ImageFile
from OFS import misc_ as icons

from silva.core.services.base import SilvaService
from silva.translations import translate as _
from zeam.form import silva as silvaforms

from silva.core.contentlayout.interfaces import IContentLayoutService
from silva.core.contentlayout.templates.interfaces import ITemplate

class ContentLayoutService(SilvaService):
    meta_type = 'Silva Content Layout Service'
    grok.implements(IContentLayoutService)
    default_service_identifier = 'service_contentlayout'

    security = ClassSecurityInfo()
    
    manage_options = (
        {'label':'Mappings',
         'action':'manage_main'},
        {'label':'Templates',
         'action':'manage_templates'}
        ) + SilvaService.manage_options

    def __init__(self, id):
        super(ContentLayoutService, self).__init__(id)
        self._content_mapping = PersistentMapping()
        
    security.declareProtected('Access contents information', 'get_templates')
    def get_templates(self):
        """return all registered ITemplates
        """
        return getUtilitiesFor(ITemplate)
    
    security.declareProtected('Access contents information', 
                              'get_sorted_templates')
    def get_sorted_templates(self):
        """returns the list of templates, sorted by their priority
        """
        templates = [ (t[1].priority, t[1].name, t[0], t)  for \
                      t in self.get_templates() ]
        return [ t[-1] for t in sorted(templates) ]
    
    security.declareProtected('Access contents information', 
                              'get_template_by_name')
    def get_template_by_name(self, name):
        """returns the ITemplate with the given name
        """
        return getUtility(ITemplate, name)
    
    security.declareProtected('Access contents information', 
                              'get_default_template_for_meta_type')
    def get_default_template_for_meta_type(self, meta_type):
        """return the default template for ``meta_type``
        """
        logger.info("no default templates yet")
        return None
        if self._content_template_mapping.has_key(meta_type):
            return self._content_template_mapping[meta_type].get('default', None)
        
    security.declareProtected('Access contents information',
                              'get_allowed_templates_for_meta_type')
    def get_allowed_templates_for_meta_type(self, meta_type):
        """return the list of allowed templates for ``meta_type``
        """
        logger.info("allowed templates not configured yet")
        #for now, just return all templates
        return [ a[0] for a in self.get_sorted_templates() ]
        
        allowed = self._content_template_mapping.get(meta_type,{}).get('allowed',[])
        if not allowed:
            return [ t[0] for t in self.get_templateTuples() ]
        return allowed

InitializeClass(ContentLayoutService)

    
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
        self.templates = self.context.get_templates()

        

class TemplateIcons(grok.View):
    grok.context(IContentLayoutService)
    grok.require("silva.ReadSilvaContent")
    grok.name('templateicons.css')
    
    def register_icon(self, name, template):
        """register the template's icon.  This takes the 'icon' attribute
           (which is a path relative to the package directory), creates
           and ImageFile from it, and registers that ImageFile as an icon
           in the misc_ namespace.  This code is generally copied from
           Products.Silva.zcml.handlers.registerIcon"""
        #skip if no icon is defined for this template, or if the
        # icon is already initialized
        if not template.icon or hasattr(template,'real_icon'):
            return
        #when the template lives in an egg, template.__module__ is zope.component.zcml
        # so use template.__class__.__module__ (which appears to be correct)
        __import__(template.__class__.__module__)
        t_module = sys.modules[template.__class__.__module__]
        t_file = t_module.__file__
        dirpath = os.path.dirname(t_file)
        iconpath = os.path.join(dirpath, template.icon)
        
        (iconPrefix, iconName) = os.path.split(iconpath)
        icon = ImageFile(iconName, iconPrefix)
        icon.__roles__ = None
        extension_name = '.'.join(template.__class__.__module__.split('.')[:-1])
        if not hasattr(icons.misc_, extension_name):
            setattr(icons.misc_, extension_name,
                    icons.Misc_(extension_name, {}))
        getattr(icons.misc_, extension_name)[iconName] = icon
        webPath = 'misc_/%s/%s' % (extension_name, iconName)

        template.__class__.real_icon = icon
        template.__class__.real_icon_path = iconpath
        template.__class__.real_icon_web_path = webPath
        
    def render(self):
        """return a css file with all icons mapped to specifiers"""
        templates = self.context.get_templates()
        response = self.request.RESPONSE
        response.setHeader("content-type","text/css;charset=utf-8")
        css = []
        css_template = u"""
.%s-icon {
background-image: url("%s");
}"""
        for (name, template) in templates:
            if template.icon:
                self.register_icon(name, template)
                name = name.replace('.','')
                css.append(css_template%(name, template.real_icon_web_path))
                #response.write(output.encode('utf-8'))
        return u'\n'.join(css)