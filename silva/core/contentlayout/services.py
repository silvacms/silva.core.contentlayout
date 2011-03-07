# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

import sys, os
from logging import getLogger
logger = getLogger('silva.core.contentlayout.services')

from five import grok
from zope.component import getUtility, getUtilitiesFor
from zope.interface import Interface, alsoProvides
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope import schema
from persistent.mapping import PersistentMapping

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.ImageFile import ImageFile
from OFS import misc_ as icons

from Products.Silva.Folder import meta_types_for_interface
from Products.Silva import SilvaPermissions
from silva.core.services.base import SilvaService
from silva.core import conf as silvaconf
from silva.translations import translate as _
from zeam.form import silva as silvaforms
from zeam.form.base.fields import Fields
from zeam.form.base.datamanager import BaseDataManager

from silva.core.contentlayout.interfaces import (IContentLayoutService,
                                                 IStickyContentService)
from silva.core.contentlayout.interfaces.schema import templates_source
from silva.core.interfaces import IContentLayout, IVersionedContentLayout
from silva.core.contentlayout.templates.interfaces import ITemplate

class StickyContentService(SilvaService):
    meta_type = "Silva Sticky Content Service"
    grok.implements(IStickyContentService)
    default_service_identifier = 'service_stickycontent'

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
        self._template_mapping = PersistentMapping()
        
    security.declareProtected('Access contents information', 'get_templates')
    def get_templates(self):
        """return all registered ITemplates
        """
        return getUtilitiesFor(ITemplate)
    
    security.declareProtected('Access contents information', 
                              'get_sorted_templates')
    def get_sorted_templates(self):
        """returns the list of templates, sorted by their priority, then name
           then dotted-name
        """
        templates = [ (t[1].priority, t[1].name, t[0], t)  for \
                      t in self.get_templates() ]
        return ( t[-1] for t in sorted(templates) )
    
    security.declareProtected('Access contents information', 
                              'get_template_by_name')
    def get_template_by_name(self, name):
        """returns the ITemplate with the given name
        """
        return getUtility(ITemplate, name)
    
    security.declareProtected('Access contents information', 
                              'get_default_template_for_meta_type')
    def get_default_template(self, meta_type):
        """return the default template name for ``meta_type``
        """
        if self._template_mapping.has_key(meta_type):
            return self._template_mapping[meta_type].get('default', None)
        
    security.declareProtected('Access contents information',
                              'get_allowed_templates_for_meta_type')
    def get_allowed_templates(self, meta_type):
        """return the list of allowed templates for ``meta_type``
        """
        allowed = self._template_mapping.get(meta_type,{}).get('allowed',[])
        st = self.get_sorted_templates()
        if not allowed:
            return stt
        return ( t for t in st if t[0] in allowed )
    
    def get_allowed_template_names(self, meta_type):
        """Get just the name for each allowed template"""
        at = self.get_allowed_templates(meta_type)
        return (t[0] for t in at)

    security.declareProtected('Access contents information',
                               'get_supporting_meta_types')
    def get_supporting_meta_types(self):
        mts = meta_types_for_interface(IVersionedContentLayout) + \
            meta_types_for_interface(IContentLayout)
        mts.sort()
        return mts
    
    security.declareProtected(SilvaPermissions.ViewManagementScreens,
                              'set_default_template')
    def set_default_template(self, meta_type, default):
        """Set the default template for the given meta_type.
          This is either the dotted-name of the template or None
        """
        if not self._template_mapping.has_key(meta_type):
            m = PersistentMapping({'default':None, 'allowed':set()})
            self._template_mapping[meta_type] = m
        self._template_mapping[meta_type]['default'] = default

    security.declareProtected(SilvaPermissions.ViewManagementScreens,
                              'set_default_template')
    def set_allowed_templates(self, meta_type, allowed):
        """Set the allowed templates for a meta_type.  This is a python ``set``
           type.
           
           This should be called after set_default_template, as the default
           is added to the allowed list supplied, if the default is set but
           not present in the allowed list.
        """
        if not self._template_mapping.has_key(meta_type):
            m = PersistentMapping({'default':None, 'allowed':set()})
            self._template_mapping[meta_type] = m
        m = self._template_mapping[meta_type]
        if m['default'] not in allowed:
            allowed.add(m['default'])
        self._template_mapping[meta_type]['allowed'] = allowed
InitializeClass(ContentLayoutService)

class IMappingsServiceZMILayer(IDefaultBrowserLayer):
    """Layer to add custom css to the mappings service form"""
    silvaconf.resource('mappings.css')

class IMappings(Interface):
    """Schema definition for the template mappings for a single 
       content layout type"""
    default = schema.Choice(
        title=_(u"Default Content Template"),
        description=_(u"The default content template for this type"),
        source=templates_source)
    allowed = schema.Set(
        title=_(u"Allowed Templates"),
        description=_(u"The set of allowed templates for this type"),
        value_type=schema.Choice(source=templates_source),
        required=False)

class TemplateDataManager(BaseDataManager):
    """A data manager specifically tailored to managing the templates"""
    
    def __init__(self, content, meta_type=None):
        super(TemplateDataManager, self).__init__(content)
        self.meta_type = meta_type
    
    def get(self, identifier):
        if identifier == 'default':
            return self.content.get_default_template(self.meta_type)
        elif identifier == 'allowed':
            #get just the name
            return self.content.get_allowed_template_names(self.meta_type)
        else:
            raise KeyError(identifier)
    
    def set(self, identifier, value):
        if identifier == 'default':
            self.content.set_default_template(self.meta_type,
                                              value)
        elif identifier == 'allowed':
            self.content.set_allowed_templates(self.meta_type,
                                               value)
        else:
            raise KeyError(identifier)
            
class MappingSubForm(silvaforms.ZMISubForm):
    grok.context(IContentLayoutService)
    fields = Fields(IMappings)
    fields['allowed'].mode = 'multiselect'
    prefix = "mapping"
    meta_type = None
    #we want to use the data manager to retrieve the field data
    ignoreContent = False

    def updateWidgets(self):
        super(MappingSubForm, self).updateWidgets()
    
    @silvaforms.action(u"Save Mappings", identifier="savemappings")
    def save(self):
        """save the mappings for this meta_type only.
        """
        data, errors = self.extractData()
        #get this data manager
        content = self.getContentData()
        for key, value in data.iteritems():
            content.set(key, value)
        self.status = "Mappings for %s updated."%self.meta_type
        return silvaforms.SUCCESS

class ContentLayoutMappings(silvaforms.ZMIComposedForm):
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
    
    def __init__(self, context, request):
        super(ContentLayoutMappings, self).__init__(context, request)
        #zeam.form.composed.SubFormGroupBase gathers subforms using
        # adaptation.  We, however, can't use adaptation as we have an
        # arbitrary number of subforms -- all being the same subform
        # operating on different data sets.
        # dynamically gather the subforms here
        subforms = []
        for addable in self.context.get_supporting_meta_types():
            #override the content for this subform, so the custom
            # datamanager is used instead
            template_dm = TemplateDataManager(self.context, addable)
            sf = MappingSubForm(self.context, self, self.request)
            sf.setContentData(template_dm)
            sf.label = addable
            sf.prefix = addable.replace(' ', '')
            sf.meta_type = addable
            subforms.append(sf)
        self.allSubforms = subforms
        self.subforms = filter(lambda f: f.available(), self.allSubforms)
    
    def update(self):
        alsoProvides(self.request, IMappingsServiceZMILayer)
        super(ContentLayoutMappings, self).update()

class TemplateIcons(grok.View):
    """return a css file with all icons mapped to specifiers"""
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