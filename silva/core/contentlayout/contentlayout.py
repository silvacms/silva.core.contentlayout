from five import grok
from zope.interface import implements
from zope.component import getUtility
from zope.app.container.interfaces import IObjectAddedEvent

from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.ObjectManager import ObjectManager

from Products.Silva import SilvaPermissions
from silva.core.interfaces import IVersion

from interfaces import IContentLayout, IContentLayoutService

class ContentLayout(ObjectManager):
    """A ContentLayout stores the layout template name (z3 utility name)
       and a set of ContentLayoutParts.  Each part is stored objectmanager-style
       via setObj.  The relationship between parts and the slots they are in
       are maintained via persistentmappings of slotname:[partid,].  When the
       part is actually needed, it is looked up via getOb.
    """
    """XXX in grok, should this *still* inherit ObjectManager?"""
    grok.implements(IContentLayout)
    grok.baseclass()
    
    security = ClassSecurityInfo()

    def __init__(self, *args, **kw):
        #mapping of slotname : [ordered list of ContentPart Keys ]
        self.content_slots = PersistentMapping()
        # mapping of partkey : slotname
        self.content_parts = PersistentMapping()
        self.content_layout_name = None
        
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_layout_name")
    def get_layout_name(self):
        return self.content_layout_name
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_slot")
    def get_slot(self, slotname, create=True):
        """get the slot with name `slotname`.  If `create` is true (default),
           and there is no slot with given name, create the slot (i.e.
           PersistentList).  If false, return false.  This enables tests
           like (does the slot exist?) without side-effects.
        """
        if create and not self.content_slots.has_key(slotname):
            self.content_slots[slotname] = PersistentList()
        return self.content_slots.get(slotname, None)

    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_slot_name_for_part")
    def get_slot_name_for_part(self, part):
        return self.content_parts[part.getKey()]

    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "add_part_to_slot")
    def add_part_to_slot(self, part, slotname, beforepartkey=None):
        if not IContentLayoutPart.providedBy(part):
            raise AttributeError("Invalid part assignment")
        if not slotname:
            raise TypeError('slotname cannot be nothing')
        if hasattr(part, 'aq_base'):
            part = part.aq_base
        partkey = part.get_key()
        
        if self.content_parts.get(partkey, slotname) is not slotname:
            raise TypeError('Part already exists in another slot')

        #if the part exists, just update the slotname
        # (this can happen if the part is moving slots)
        self.content_parts[partkey] = slotname
        slot = self.get_slot(slotname)
        #remove the partkey if it was already in the slot
        if partkey in slot:
            del slot[slot.index(partkey)]
        if beforepartkey is None:
            slot.append(partkey)
        else:
            slot.insert(slot.index(beforepartkey), 
                         partkey)
        if not self.hasObject(str(partkey)):
            self._setObject(str(partkey), part)
        part = getattr(self.aq_explicit, str(partkey))
        return part
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "remove_part")
    def remove_part(self, partkey):
        slotname = self.content_parts[partkey]
        del self.content_parts[partkey]
        slot = self.get_slot(slotname)
        del slot[slot.index(partkey)]
        self._delObject(str(partkey))
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "move_part_to_slot")
    def move_part_to_slot(self, partkey, slotname, beforepartkey=None):
        """Moving an existing part to a new slot, using this algorithm:
                remove the part from the part's old slot
                add part to the new slot
                [part, slot]
        """
        oldslotname = self.content_parts[partkey]
        oldSlot = self.get_slot(oldslotname)
        del oldSlot[oldSlot.index(partkey)]
        part = getattr(self.aq_explicit, str(partkey))
        del self.content_parts[partkey]
        self.add_part_to_slot(part, slotname, beforepartkey)
     
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_parts_for_slot")
    def get_parts_for_slot(self, slot):
        """get all parts in slot, returning as a list generator"""
        slot = self.get_slot(slot)
        return ( getattr(self.aq_explicit, str(partkey)) for partkey in slot )
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_part")
    def get_part(self, partkey):
        return getattr(self.aq_explicit, str(partkey), None)
    
    
    security.declareProtected(SilvaPermissions.AccessContentsInformation,
                              "get_parts")
    def get_parts(self):
        """get all all parts"""
        return ( getattr(self.aq_explicit, str(partkey)) for partkey in self.content_parts )
    
    security.declareProtected(SilvaPermissions.ChangeSilvaContent,
                              "switch_template")
    def switch_template(self, newTemplateName):
        """Switch the template to newTemplate. 
           - first get the template from service_content_templates
             (raise error if not found)
           - then move parts to the new slots.  Be smart about this this:
             1) for each slot in oldTemplate, move the parts to the slot with the
                same index (in the new template's slot list).
             2) Any slots in oldTemplate which don't have a corresponding slot
                in newTemplate are placed in the last slot in newTemplate
        """
        #XXX this needs to be fixed
        newTemplate = self.service_content_templates.get_template_by_name(newTemplateName)
        oldTemplate = self.service_content_templates.get_template_by_name(self.content_layout_name)
        newSlots = PersistentMapping()
        newNames = newTemplate.slotnames[:]
        #pull the keys from the model's slotnames rather than the slotnames
        # from the old template (in case the slotnames in the old template
        # have changed, we'll loose data)
        oldNames = self.content_slots.keys()
        #oldName = oldTemplate.slotnames[:]
        newslotname = newNames.pop(0)
        while(oldNames):
            oldslotname = oldNames.pop(0)
            #move the parts to the new slot
            if not newSlots.has_key(newslotname):
                newSlots[newslotname] = PersistentList()
            newslot = newSlots[newslotname]
            if not self.content_slots.has_key(oldslotname):
                #skip out of the switching if the old datastructures
                # did not have the old slot name.  This could happen
                # on content creation, where the template was initially
                # created with one template (but the data structures
                # were not setup)
                continue
            newslot.extend(self.content_slots[oldslotname])
            
            #update the part structures to refer to the new slot
            for partkey in self.content_slots[oldslotname]:
                self.content_parts[partkey] = newslotname
            del self.content_slots[oldslotname]
            
            if oldNames and newNames:
                newslotname = newNames.pop(0)
            else:
                #otherwise, keep the last newslotname
                pass
            
        if newNames:
            #initialize the other slots for this layout
            for newslotname in newNames:
                newSlots[newslotname] = PersistentList()
        self.content_slots = newSlots
        self.content_layout_name = newTemplateName
InitializeClass(ContentLayout)


@grok.subscribe(IContentLayout, IObjectAddedEvent)
def layout_added(content, event):
    """called when a ContentLayout object is added to an object manager
    if no layout has been set yet, set it's layout to the default layout
    from the layout service.
    """
    if content.content_layout_name == None:
        #this should only be None when the content is first created.
        # another possible check would be to see if event.oldName and/or 
        # event.oldParent are None (there was no previous parent, so new object)
        cls = getUtility(IContentLayoutService)
        orig_content = content
        if IVersion.providedBy(content):
            #the template settings are stored by the VersionedContent meta_type,
            # not the Version meta_type
            content = content.aq_parent
        default = cls.getDefaultTemplateForMetaType(content.meta_type)
        if not default: #no default is set, so get the first one
            default = cls.getAllowedTemplatesForMetaType(content.meta_type)[0]
        orig_content.content_layout_name = default