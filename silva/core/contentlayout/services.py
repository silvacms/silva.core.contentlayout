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
from persistent.list import PersistentList
from zope.cachedescriptors.property import CachedProperty

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.ImageFile import ImageFile
from OFS import misc_ as icons
from OFS.Folder import Folder

from Products.Silva.Folder import meta_types_for_interface
from Products.Silva import SilvaPermissions
from silva.core.services.base import SilvaService
from silva.core import conf as silvaconf
from silva.translations import translate as _
from silva.core.smi import smi
from silva.core.smi.interfaces import IPropertiesTab
from zeam.form import silva as silvaforms
from zeam.form.base.fields import Fields
from zeam.form.base.datamanager import BaseDataManager
    
from silva.core.interfaces import (IContentLayout, IVersionedContentLayout,
                                   IPublication, ISiteManager, IRoot)
from silva.core.contentlayout.interfaces import (IContentLayoutService,
                                                 IStickyContentService,
                                                 IStickyContentLayout,
                                                 IPartFactory,
                                                 IStickySupport)
from silva.core.contentlayout.contentlayout import ContentLayout
from silva.core.contentlayout.interfaces.schema import templates_source
from silva.core.contentlayout.templates.interfaces import ITemplate

class StickyServiceButton(smi.SMIMiddleGroundButton):
    """middle ground button to access the sticky content service within
       the SMI"""
    grok.view(IPropertiesTab)
    grok.context(IPublication)
    grok.require('silva.ManageSilvaContentSettings')
    
    tab = 'tab_sticky_content'
    label = _(u"sticky content")
    help = _(u"manage the sticky content applied to this container")


class StickyContentService(SilvaService, Folder):
    meta_type = "Silva Sticky Content Service"
    grok.implements(IStickyContentService)
    default_service_identifier = 'service_sticky_content'
    
    security = ClassSecurityInfo()
    
    manage_options = (
        {'label':'Sticky Content',
         'action':'manage_sticky'},
        ) + SilvaService.manage_options
    
    def __init__(self, id):
        super(StickyContentService, self).__init__(id)
        self._sticky_content = PersistentMapping()
        
    
    def _getStickyContentLayout(self, layout, create=True):
        """get the StickyContentLayout for `layout` (the name of the layout).
           if `create` and a StickyContentLayout does not exist, create one.
           (so this method can also be used to determine if sticky content
            exists (anywhere) for a layout)
        """
        #needs to be a str (not ustr)
        layout = str(layout)
        if create and not self.hasObject(layout):
            sl = StickyContentLayout(layout)
            self._setObject(layout, sl)
        return getattr(self.aq_explicit,layout,None)
        

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "getBlockedPartsForLayout")
    def getBlockedPartsForLayout(self, layout):
        """returns the list of blocked parts for ``layout``
        """
        layout = self._getStickyContentLayout(layout, create=False)
        if not layout:
            return []
        return layout.get_blocked_parts()
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "getStickyContentForLayoutSlot")
    def getStickyContentForLayoutSlot(self, layout, slot):
        """get the sticky content in the `slot` in the `layout`.
           will return an empty list if there is no 
           sticky content.
           Return value 1-tuple of [acquired] + [local]
        """
        stickies = self.getStickyContentForLayoutSlot_split(layout, slot)
        return stickies[0] + stickies[1]
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "getStickyContentForLayoutSlot_split")
    def getStickyContentForLayoutSlot_split(self, layout, slot):
        """get the sticky content in the `slot` in the `layout`.
           will return an empty list if there is no 
           sticky content.
           Return value is a 2-tuple: [ [acquired], [local] ]
        """
        acquired_parts = []
        blocked_parts = self.getBlockedPartsForLayout(layout)
        
        #first get the acquired parts
        container = self.aq_inner.aq_parent
        if not IRoot.providedBy(container) and \
           hasattr(container.aq_parent, self.id):
            parent_parts = getattr(container.aq_parent, self.id).getStickyContentForLayoutSlot(layout, slot)
            acquired_parts.extend( [ p for p in parent_parts
                                     if p.get_key() not in blocked_parts ] )
        
        layout = self._getStickyContentLayout(layout, create=False)
        if not layout: 
            #only acquired parts
            return [ acquired_parts, [] ]
        
        #this only returns a list of [acquired, local] sticky parts.
        # somehow, this needs to be sorted in a way that allows
        # order (top, bottom), and is easy to determine whether
        # a part is acquired or not.
        
        ordered_parts = [ (IStickySupport(p).get_placement(), i, p) for i,p in 
                          enumerate(layout.get_parts_for_slot(slot)) ]
        ordered_parts.sort()

        return [ acquired_parts,  [ p[2] for p in ordered_parts ] ]
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "getPlacementForStickyContent")
    def getPlacementForStickyContent(self, part):
        ad = IStickySupport(part)
        return ad.get_placement()

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "changePlacementForStickyContent")
    def changePlacementForStickyContent(self, layout, partkey, current):
        sticky_layout = self._getStickyContentLayout(layout)
        part = sticky_layout.get_part(partkey)
        
        ad = IStickySupport(part)
        if current=='above':
            ad.change_placement('below')
        else:
            ad.change_placement('above')
            
    def getStickyContent(self, layout, partkey, acquire=True):
        sticky_layout = self._getStickyContentLayout(layout)
        part = sticky_layout.get_part(partkey)

        #return part or None if part or we're not acquiring
        if part or not acquire:
            return part
        
        container = self.aq_inner.aq_parent
        if not IRoot.providedBy(container) and \
           hasattr(container.aq_parent, self.id):
            ssc = getattr(container.aq_parent, self.id)
            return ssc.getStickyContent(layout, partkey)
        return None

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "hasStickyContentForLayout")
    def hasStickyContentForLayout(self, layout):
        """return True if service has sticky content for `layout`, in 
           _any_ slot
        """
        layout = self._getStickyContentLayout(layout, create=False)
        return not not layout
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "hasStickyContentForLayoutSlot")
    def hasStickyContentForLayoutSlot(self, layout, slot):
        """return True if service has sticky content for `layout` in
           `slot`
        """
        layout = self._getStickyContentLayout(layout, create=False)
        if not layout:
            return False
        #this will return None if the slot does not exist (preventing 
        # side-effect of creating the slot
        slot = layout.get_slot(slot, create=False)
        return not slot or len(slot)>0
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "addStickyContent")
    def addStickyContent(self, layoutname, part, slotname, beforepartkey=None):
        """Add a Sticky Content Part to the template `template_name`
        Sticky Content Parts are ContentLayoutParts which are
        instances of cs_page_asset (every sticky content is a page asset)
        """
        sticky_layout = self._getStickyContentLayout(layoutname)
        part = sticky_layout.add_part_to_slot(part, slotname, beforepartkey)
        return part
    
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "removeStickyContent")
    def removeStickyContent(self, layoutname, partkey):
        """remove a local sticky content from a layout"""
        sticky_layout = self._getStickyContentLayout(layoutname)
        sticky_layout.remove_part(partkey)
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "moveStickyContent")
    def moveStickyContent(self, layoutname, partkey, beforepartkey):
        sticky_layout = self._getStickyContentLayout(layoutname)
        part = sticky_layout.get_part(int(partkey))
        slotname = sticky_layout.get_slot_name_for_part(part)
        sticky_layout.add_part_to_slot(part, slotname, int(beforepartkey))

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "blockAcquiredStickyContent")
    def blockAcquiredStickyContent(self, template_name, partkey):
        """block an acquired sticky content part for a template, given
        the parts key"""
        self._getStickyContentLayout(template_name).add_blocked_part(partkey)
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "unblockAcquiredStickyContent")
    def unblockAcquiredStickyContent(self, template_name, partkey):
        """block an acquired sticky content part for a template, given
        the parts key"""
        self._getStickyContentLayout(template_name).remove_blocked_part(partkey)
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "manage_block")
    def manage_block(self, layout, partkey):
        """ZMI function to block acquired content"""
        self.blockAcquiredStickyContent(layout, int(partkey))
        return self.manage_sticky(manage_tabs_message="part blocked")

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "manage_unblock")
    def manage_unblock(self, layout, partkey):
        """ZMI function to block acquired content"""
        self.unblockAcquiredStickyContent(layout, int(partkey))
        return self.manage_sticky(manage_tabs_message="part no longer blocked")

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "manage_remove")
    def manage_remove(self, layout, partkey):
        """ZMI function to block acquired content"""
        partkey = int(partkey)
        self.removeStickyContent(layout, partkey)
        return self.manage_sticky(manage_tabs_message="part removed from %s"%layout)
    
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "manage_remove")
    def manage_move(self, layout, partkey, beforepartkey):
        """ZMI function to move local content in a slot"""
        partkey = int(partkey)
        beforepartkey = int(beforepartkey)
        self.moveStickyContent(layout, partkey, beforepartkey)
        return self.manage_sticky(manage_tabs_message="part moved")

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "manage_addStickyContent")
    def manage_addStickyContent(self, result, layout, slot):
        """Create a cs_page_asset part and add it as sticky content
        to the ``layout``:``slot``"""
        #use a factory to create the ContentLayoutPart, so that different
        # external sources can have different Parts.
        source = getattr(self.aq_inner, 'cs_page_asset')
        factory = IPartFactory(source)
        part = factory.create(result)

        self.addStickyContent(layout,
                              part,
                              slot
                              )
InitializeClass(StickyContentService)


class StickyMacros(grok.View):
    """a macro view / page template for tab_sticky_content"""
    grok.context(IStickyContentService)

    
class StickyContentLayout(ContentLayout):
    """StickyContentLayout stores the sticky content parts for a
       template
    """
    grok.implements(IStickyContentLayout)
    security = ClassSecurityInfo()
    
    def __init__(self, name):
        super(StickyContentLayout, self).__init__()
        #set the layout/template name
        self._content_layout_name = name
        self._blocked_parts = PersistentList()
        
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_blocked_parts")
    def get_blocked_parts(self):
        """ returns the blocked parts as a list
        """
        return list(self._blocked_parts)
    
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "add_blocked_part")
    def add_blocked_part(self, partkey):
        """add a parts (it's key) to the list of blocked parts
        """
        if partkey not in self._blocked_parts:
            self._blocked_parts.append(partkey)
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "remove_blocked_part")
    def remove_blocked_part(self, partkey):
        """remove a part (it's key) from the list of blocked parts
        """
        if partkey in self._blocked_parts:
            self._blocked_parts.remove(partkey)
InitializeClass(StickyContentLayout)


#class StickyContentForm(silvaforms.SMIComposedForm):
    #"""outer "form" to manage sticky content"""
    #grok.context(IPublication)
    #grok.implements(IPropertiesTab)
    #grok.name('tab_sticky_content')
    #grok.require('silva.ManageSilvaContent')
    
    #tab = "properties"

    #label = _(u"Sticky Content Layout")
    #description = _(u"This tab provides for managing sticky content. "
                    #u"Sticky content is a chunk of content (e.g. a widget) "
                    #u"which is always present on content layout templates "
                    #u"within this container.")
    
    #def __init__(self, context, request):
        #super(StickyContentForm, self).__init__(context, request)
        ##zeam.form.composed.SubFormGroupBase gathers subforms using
        ## adaptation.  We, however, can't use adaptation as we have an
        ## arbitrary number of subforms -- all being the same subform
        ## operating on different data sets.
        ## dynamically gather the subforms here
        ## but note we also have normal subforms
        #extrasubforms = []
        #sct = getUtility(IContentLayoutService)
        #for (id,template) in sct.get_sorted_templates():
            #sf = ManageStickyContentSubForm(self.context, self, self.request)
            #sf.template = template
            #sf.template_id = id
            #sf.prefix = id
            #sf.label = "Edit Sticky Content for " + template.name
            #extrasubforms.append(sf)
        #self.allSubforms = extrasubforms + self.allSubforms
        
        #self.subforms = filter(lambda f: f.available(), self.allSubforms)
        
#class StickyFormBase(object):
    #"""Base class with Helper methods common to all 
       #subforms of StickyContentForm
    #"""
    
    #@property
    #def has_sticky(self):
        #return hasattr(self.context.aq_explicit, 
                       #'service_sticky_content')
    
#class ManageStickyContentSubForm(StickyFormBase, silvaforms.SMISubForm):
    #"""This is a subform, but it doesn't have an explicit view.  An instance
       #of this subform manages the sticky content for a single template.
       #Instances are created when StickyContentForm is initialized
    #"""
    #grok.order(100)
    #grok.context(IPublication)

    #prefix = "sticky"
    #label = _(u"Edit Sticky Content")
    #description = _(u"use this form to edit sticky content")
    
    #def available(self):
        #"""although this form has no grok.view, it is still associated
           #(implicitly) to StickyContentForm.  We don't want this 'default'
           #content form to show up, so suppress it (if the prefix is unchanged
        #"""
        #return self.prefix != 'sticky' and self.has_sticky
    
#class RemoveStickyContentSubForm(StickyFormBase, silvaforms.SMISubForm):
    #"""Form to remove the sticky content service from an IPublication.
       #Not available in the Root.
       #Will attempt to remove the IPublication as a local site
    #"""
    #grok.view(StickyContentForm)
    #grok.order(30)
    #grok.context(IPublication)
    
    #label = _(u"Remove Local Sticky Content Service")
    #description = _(u"This container has a sticky content service. "
                    #u"If desired, you can be remove it using this form.")

    
    #def available(self):
        #"""This form is not available in the Silva root"""
        #return self.has_sticky and not IRoot.providedBy(self.context)

    #def remove_available(self):
        #return self.has_sticky
    #@silvaforms.action(_(u"remove"),
                       #description=_(u"remove the local sticky content service"),
                       #available=remove_available)
    #def remove(self):
        #if self.has_sticky:
            #self.context.manage_delObjects(['service_sticky_content'])
            #sm = ISiteManager(self.context)
            #if sm.isSite():
                #try:
                    ##this will fail with a ValueError if the site cannot
                    ## be deleted
                    #sm.deleteSite()
                #except ValueError:
                    #pass
            #self.send_message(_(u"Service removed"), type=u"feedback")
            #return silvaforms.SUCCESS
        #else:
            #self.send_message(_(u"Unable to remove service: does not exist"), type=u"error")
            #return silvaforms.FAILURE

#class AddStickyContentSubForm(StickyFormBase, silvaforms.SMISubForm):
    #"""Form to add the sticky content service to an IPublication.
       #Not available in the Root.
       #Will make the IPublication a local site before adding the service.
    #"""
    
    #grok.view(StickyContentForm)
    #grok.order(30)
    #grok.context(IPublication)
    
    #label = _(u"Create Local Sticky Content Service")
    #description = _(u"This container does not have a sticky content service. "
                    #u"Create one to start using sticky content.")
    
    #def available(self):
        #"""This form is not available in the Silva root"""
        #return not (self.has_sticky or IRoot.providedBy(self.context))

    #def add_available(self):
        #return not self.has_sticky
    #@silvaforms.action(_(u"create"),
                       #description=_(u"add a local sticky content service"),
                       #available=add_available)
    #def add(self):
        #if not self.has_sticky:
            ##make context a local service, if it isn't already
            #sm = ISiteManager(self.context)
            #if not sm.isSite():
                #sm.makeSite()
            #self.context.manage_addProduct['silva.core.contentlayout'].manage_addStickyContentService()
            #self.send_message(_(u"Service created"), type=u"feedback")
            #return silvaforms.SUCCESS
        #else:
            #self.send_message(_(u"Service already exists"), type=u"error")
            #return silvaforms.FAILURE
        
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
                              'get_default_template')
    def get_default_template(self, meta_type):
        """return the default template name for ``meta_type``
        """
        if self._template_mapping.has_key(meta_type):
            return self._template_mapping[meta_type].get('default', None)
        
    security.declareProtected('Access contents information',
                              'get_allowed_templates')
    def get_allowed_templates(self, meta_type):
        """return the list of allowed templates for ``meta_type``
        """
        allowed = self._template_mapping.get(meta_type,{}).get('allowed',[])
        st = self.get_sorted_templates()
        if not allowed:
            return st
        return ( t for t in st if t[0] in allowed )
    
    security.declareProtected('Access contents information',
                              'get_allowed_template_names')
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
        #add default to allowed if allowed is not empty.
        # (if it is empty, all templates are allowed)
        if allowed and m['default'] not in allowed:
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
    
pass #improved code folding support in wing