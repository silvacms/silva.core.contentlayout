from ContentLayoutTestCase import ContentLayoutTestCase

from zExceptions import NotFound

from silva.core.contentlayout.parts import ExternalSourcePart
from silva.core.contentlayout.interfaces import IPartFactory
from zope.component.interfaces import ComponentLookupError

class ContentLayoutClassTestCase(ContentLayoutTestCase):
    
    def afterSetUp(self):
        super(ContentLayoutClassTestCase, self).afterSetUp()
        self.layoutName = 'silva.contentlayouttemplates.twocolumn'
      
        #copy an external source into the root
        self.installExtension("SilvaExternalSources")
        self.login('manager')
        token = self.root.service_codesources.manage_copyObjects(["cs_multitoc"])
        self.root.manage_pasteObjects(token)
        self.login('chiefeditor')
        
    def test_LayoutName(self):
        
        # test to make sure switching template works
        e = self.page.get_editable()
        e.switchTemplate(self.layoutName)
        self.assertEquals(self.layoutName, e.getLayoutName())
        #Test to make sure invalid template name raises error
        self.assertRaises(ComponentLookupError, e.switchTemplate, ';lkasj')
        
    def test_SlotName(self):
        
        e = self.page.get_editable()
        e.switchTemplate(self.layoutName)
        #Make sure the slot name initially does not exist
        self.assertEquals(None, e.getSlot('feature', False))
        #Confirm slot is created empty
        self.assertEquals([], e.getSlot('feature', True))

    def test_addPartToSlot(self):
        e = self.page.get_editable()
        cs = getattr(self.root, 'cs_multitoc')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        self.assertRaises(TypeError, e.addPartToSlot, part, None)

    def test_PartsForSlot(self):
        e = self.page.get_editable()
        e.switchTemplate(self.layoutName)
        e.getSlot('feature', True)
        #Make sure there are no parts in slot
        self.assertEquals(0, len(list(e.getPartsForSlot('feature'))))
        
        cs = getattr(self.root, 'cs_multitoc')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        part2 = factory.create({'paths':'pub2'})
        e.addPartToSlot(part, 'feature')
        #Make sure there is only one part in slot
        self.assertEquals(1, len(list(e.getPartsForSlot('feature'))))
        e.removePart(part.getKey())
        #Make sure part was removed properly
        self.assertEquals(0, len(list(e.getPartsForSlot('feature'))))
        #Make sure removing a part not in slot fails
        self.assertRaises(KeyError, e.removePart,part.getKey())

        e.addPartToSlot(part, 'feature')
        e.movePartToSlot(part.getKey(), 'left')
        #Make sure moving parts between slots works
        self.assertEquals(0, len(list(e.getPartsForSlot('feature'))))
        self.assertEquals(1, len(list(e.getPartsForSlot('left'))))
        
        #Make sure that trying to add duplicate part doesn't work
        self.assertRaises(TypeError, e.addPartToSlot, part, 'feature')
       
        e.removePart(part.getKey())
        e.addPartToSlot(part, 'feature')
        e.addPartToSlot(part2, 'feature')
        #Make sure we can add multiple parts to slot
        self.assertEquals(2, len(list(e.getPartsForSlot('feature'))))
   
        
        
    def test_getParts(self):
        e = self.page.get_editable()
        e.switchTemplate(self.layoutName)
        e.getSlot('feature', True)
        #Make sure there are no parts in slot
        self.assertEquals(0, len(list(e.getPartsForSlot('feature'))))
        cs = getattr(self.root, 'cs_multitoc')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        part2 = factory.create({'paths':'pub2'})
        e.addPartToSlot(part, 'feature')
        e.addPartToSlot(part2, 'panel' )
        
        self.assertEquals(2, len(list(e.getParts())))
        self.assertRaises(TypeError, 3, len(list(e.getParts())))
        
    def test_slotNameForPart(self):
        e = self.page.get_editable()
        e.switchTemplate(self.layoutName)
        e.getSlot('feature', True)
       
        cs = getattr(self.root, 'cs_multitoc')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        
        e.addPartToSlot(part, 'feature')
        #Make sure we can get correct slot a part is in
        self.assertEquals('feature', e.getSlotNameForPart(part))
        #Make sure that proper error is raised if a part is not specified
        self.assertRaises(AttributeError, e.getSlotNameForPart, None)

    def test_SwitchTemplate(self):
        e = self.page.get_editable()
        e.switchTemplate(self.layoutName)
        self.assertEquals(self.layoutName, e.getLayoutName())
        #Test to see if we can switch to same template
        e.switchTemplate(self.layoutName)
        self.assertEquals(self.layoutName, e.getLayoutName())
        
        cs = getattr(self.root, 'cs_multitoc')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        part2 = factory.create({'paths':'pub2'})
        e.addPartToSlot(part, 'panel')
        e.addPartToSlot(part2, 'panel')
        
        #Switch templates multiple times to make sure parts move properly
        e.switchTemplate('silva.contentlayouttemplates.onecolumn')
        e.switchTemplate('silva.contentlayouttemplates.twocolumn')
        e.switchTemplate('silva.contentlayouttemplates.onecolumn')
        e.switchTemplate('silva.contentlayouttemplates.twocolumn')
        self.assertEquals('silva.contentlayouttemplates.twocolumn', e.getLayoutName())
        # test to make sure the parts are in the correct slot
        self.assertEquals(2, len(list(e.getPartsForSlot('feature'))))

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContentLayoutClassTestCase))
    return suite
