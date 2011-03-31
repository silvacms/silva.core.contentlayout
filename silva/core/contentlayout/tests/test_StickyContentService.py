from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

from silva.core.interfaces import ISiteManager
from silva.core.conf.utils import getSilvaViewFor
from silva.core.smi.interfaces import ISMILayer
from silva.core.contentlayout.parts import ExternalSourcePart
from silva.core.contentlayout.interfaces import IStickySupport

from ContentLayoutTestCase import ContentLayoutTestCase


class StickyContentServiceTestCase(ContentLayoutTestCase):
    
    def setUp(self):
        super(StickyContentServiceTestCase, self).setUp()
        #the root service is added during Silva install
        self.root_service = self.root.service_sticky_content
        
        #make pub1 a local site so it can contain a sticky content service
        ISiteManager(self.pub1).makeSite()
        self.pub1.manage_addProduct['silva.core.contentlayout'].manage_addStickyContentService()
        self.pub1_service = self.pub1.service_sticky_content
        
        self.t_name = "silva.core.contentlayout.templates.OneColumn"
        self.slotname = 'maincontent'
        
    def createPart(self, asset, placement="above"):
        #create and return a Sticky ContentPart
        return ExternalSourcePart('cs_page_asset',
                                  { "object_path":'/'.join(asset.getPhysicalPath()),
                                    "placement":placement
                                  })

    def test_stickybutton(self):
        #verify the sticky button exists in the middleground for
        # IContainers
        request = TestRequest()
        alsoProvides(request, ISMILayer)
        view = getSilvaViewFor(self.root, 'edit', self.root)
        prop_tab = getMultiAdapter((self.root, request),
                                   name="tab_edit")
        
    def atest_StickyServiceExists(self):
        #simple test to make sure the service was added to each container
        self.assertEquals(True, 
                          hasattr(self.root, 'service_sticky_content'))
        self.assertEquals(True, 
                          hasattr(self.pub1, 'service_sticky_content'))
        
    def atest_hasStickyContent(self):
        #test to determine whether a layout has any sticky content
        self.assertEquals(False,
                self.root_service.hasStickyContentForLayout(self.t_name))
        
        self.assertEquals(False,
                self.root_service.hasStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname))
        
        #now add a part, and the tests should be True
        part = self.createPart(self.root_pa)
        part = self.root_service.addStickyContent(self.t_name, part, self.slotname)

        self.assertEquals(True,
                self.root_service.hasStickyContentForLayout(self.t_name))
        
        self.assertEquals(True,
                self.root_service.hasStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname))

    def atest_setStickyAtRoot(self):
        #set sticky content in root's service, verify it is set
        sticky_layout = self.root_service._getStickyContentLayout(self.t_name)
        
        part = self.createPart(self.root_pa)
        self.root_service.addStickyContent(self.t_name, part, self.slotname)
        
        
        partkey = part.getKey()
        self.assertEquals(part, 
                          sticky_layout.getPart(partkey))
        self.assertEquals(self.slotname, 
                          sticky_layout.getSlotNameForPart(part))
        
    def atest_getStickyContent_noaq(self):
        #test getting sticky content in the root service
        # NOTE: this does not test acquiring sticky content
        
        #before any parts are added, this should be an empty list
        emt_parts = self.root_service.getStickyContentForLayoutSlot(self.t_name, 
                                                     self.slotname)
        self.assertEquals([], emt_parts)

        #create and add sticky content 
        part1 = self.createPart(self.root_pa)
        part1 = self.root_service.addStickyContent(self.t_name, part1, self.slotname)
    
        #now this should be a list with one item
        parts = list(self.root_service.getStickyContentForLayoutSlot(self.t_name, 
                                                      self.slotname))
        self.assertEquals([part1], parts)
        
        parts2 = list(self.root_service.getStickyContentForLayoutSlot_split(self.t_name,
                                                      self.slotname))
        self.assertEquals(parts2[0], [])
        # This object is actually a ImplicitAcquirerWrapper, but there doesn't seem to be a good
        # way to get that out, so test to make sure it is a list type
        self.assertEquals(type(parts2[1]),type([]))

    def atest_stickyOrder(self):
        #add two sticky content parts in root's service, testing the order
        # (i.e. add the second before (above) the first
        
        part1 = self.createPart(self.root_pa)
        part1 = self.root_service.addStickyContent(self.t_name, part1, self.slotname)
        
        #add the second part before the first
        part2 = self.createPart(self.root_pa2)
        part2 = self.root_service.addStickyContent(self.t_name, part2, self.slotname,
                                           beforepartkey=part1.getKey())
        
        #get the sticky layout, check order of sticky parts
        #this returns a generator, so convert to a list
        parts = list(self.root_service.getStickyContentForLayoutSlot(
            self.t_name, self.slotname))
        self.assertEquals([part2,part1], parts)
    
        
        #Chech the _split version of the same method
        parts2 = list(self.root_service.getStickyContentForLayoutSlot_split(self.t_name,
                                                      self.slotname))
        self.assertEquals(parts2[0], [])
        # This object is actually a ImplicitAcquirerWrapper, but there doesn't seem to be a good
        # way to get that out, so test to make sure it is a list type 
        self.assertEquals(type(parts2[1]),type([]))

    def atest_getStickyContent_aq(self):
        #test getting sticky content in the root service
    
        root_part = self.createPart(self.root_pa)
        root_part = self.root_service.addStickyContent(self.t_name, 
                                                       root_part,
                                                       self.slotname)
        
        pub1_part = self.createPart(self.pub1_pa)
        pub1_part = self.pub1_service.addStickyContent(self.t_name, 
                                                       pub1_part,
                                                       self.slotname)
        
        parts = self.pub1_service.getStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname)
        self.assertEquals([root_part, pub1_part], parts)

    def atest_markBlockedStickyContent(self):
        # marks a sticky content part in the root service as being blocked
        # within the publication's service.
        root_part = self.createPart(self.root_pa)
        root_part = self.root_service.addStickyContent(self.t_name, 
                                                       root_part,
                                                       self.slotname)
        
        pre_parts = self.pub1_service.getStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname)
        self.assertEquals([root_part], pre_parts)

        self.pub1_service.blockAcquiredStickyContent(self.t_name, 
                                                     root_part.getKey())
        blocked_parts = self.pub1_service.getBlockedPartsForLayout(self.t_name)
        self.assertEquals([root_part.getKey()], blocked_parts)
        
        parts = self.pub1_service.getStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname)
        self.assertEquals([], parts)

    def atest_unmarkBlockedStickyContent(self):
        # first marks a sticky content part as blocked in the pub's service,
        # then unmarks it
        root_part = self.createPart(self.root_pa)
        root_part = self.root_service.addStickyContent(self.t_name, 
                                                       root_part,
                                                       self.slotname)
        self.pub1_service.blockAcquiredStickyContent(self.t_name, 
                                                     root_part.getKey())
        parts = self.pub1_service.getStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname)
        self.assertEquals([], parts)
        
        self.pub1_service.unblockAcquiredStickyContent(self.t_name,
                                                       root_part.getKey())
        parts = self.pub1_service.getStickyContentForLayoutSlot(self.t_name,
                                                                self.slotname)
        self.assertEquals([root_part], parts)
        
    def atest_moveStickyContent(self):
        # add two sticky contents to a layout
        # move the bottom one up
        # verify the order has changed
        #since the same function would be called to move content down
        # (but reversing the order of arguments), only one test is needed
        part1 = self.createPart(self.root_pa)
        part1 = self.root_service.addStickyContent(self.t_name, 
                                                   part1,
                                                   self.slotname)
        part2 = self.createPart(self.root_pa2)
        part2 = self.root_service.addStickyContent(self.t_name, 
                                                   part2,
                                                   self.slotname)
        parts = self.root_service.getStickyContentForLayoutSlot(
            self.t_name,
            self.slotname)
        
        self.assertEquals([part1,part2], parts)
        
        self.root_service.moveStickyContent(
            self.t_name,
            part2.getKey(),
            part1.getKey())
        
        parts = self.root_service.getStickyContentForLayoutSlot(
            self.t_name,
            self.slotname)
        
        self.assertEquals([part2,part1], parts)
        
    def atest_getPlacement(self):
        #test getting sticky content placement (above, below)
        
        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name, 
                                                   part1,
                                                   self.slotname)
        
        ad = IStickySupport(part1)
        self.assertEquals("above", ad.getPlacement())
        
        ad.changePlacement("below")
        self.assertEquals("below", ad.getPlacement())
        
    def atest_getPlacementForStickyContent(self):
        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name,
                                                   part1,
                                                   self.slotname)
        
        placement = part1.getPlacementForStickyContent(part1)
        self.assertEquals("above", placement)
        
        #Change it to below (different methed that used in test_getPlacement()
        part1.changePlacementForStickyContent(self.t_name, part1.getKey(), placement)

        placement = part1.getPlacementForStickyContent(part1)
        self.assertEquals("below", placement)

    def atest_hasStickyContentForLayout(self):
        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name,
                                                   part1,
                                                   self.slotname)

        #Test to see if there is sticky content in self.t_name
        self.assertEquals(part1.hasStickyContentForLayout(self.t_name), True)

        #Make sure it has no Sticky Content for a fake layout name
        self.assertEquals(part1.hasStickyContentForLayout("NotARealTemplate"), False)
        
    def atest_hasStickyContentForLayoutSlot(self):
        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name,
                                                   part1,
                                                   self.slotname)

        #Test to see if there is sticky content in self.t_name
        self.assertEquals(part1.hasStickyContentForLayoutSlot(self.t_name, "above"), True)

        #Make sure it has no Sticky Content for a fake layout name
        self.assertEquals(part1.hasStickyContentForLayoutSlot("NotARealTemplate", "above"), False)


        placement = part1.getPlacementForStickyContent(part1)
        part1.changePlacementForStickyContent(self.t_name, part1.getKey(), placement)


        #Test to see if there is sticky content in self.t_name
        self.assertEquals(part1.hasStickyContentForLayoutSlot(self.t_name, "below"), True)

        #Make sure it has no Sticky Content for a fake layout name 
        self.assertEquals(part1.hasStickyContentForLayoutSlot("NotARealTemplate", "below"), False)

        #Why is this True?
        self.assertEquals(part1.hasStickyContentForLayoutSlot(self.t_name, "NotARealSlot"), True)

    def atest_removeStickyContent(self):

        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name,
                                                   part1,
                                                   self.slotname)

        
        part1.removeStickyContent(self.t_name, part1.getKey())
        

        #Fix This
        self.assertEquals(part1.hasStickyContentForLayoutSlot(self.t_name, self.slotname), True)
        
    def atest_getBlockedParts(self):

        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name,
                                                   part1,
                                                   self.slotname)
        
        #Should start with no blocked parts
        self.assertEquals(part1.getBlockedParts(), [])
        #Add one, make sure its there
        part1.addBlockedPart(123)
        self.assertEquals(part1.getBlockedParts(), [123])        
        #Another
        part1.addBlockedPart(213)
        self.assertEquals(part1.getBlockedParts(), [123, 213])
        #And Another
        part1.addBlockedPart(231)
        self.assertEquals(part1.getBlockedParts(), [123, 213, 231])
        #Remove one, make sure its gone
        part1.removeBlockedPart(123)
        self.assertEquals(part1.getBlockedParts(), [213, 231])
        #Remove another
        part1.removeBlockedPart(213)
        self.assertEquals(part1.getBlockedParts(), [231])
        #Remove the last one
        part1.removeBlockedPart(231)
        self.assertEquals(part1.getBlockedParts(), [])

        # Should there be restrictions on what a partkey can be?
        part1.addBlockedPart('$#@!#$@#$@#$@#$')
        self.assertEquals(part1.getBlockedParts(), ['$#@!#$@#$@#$@#$'])
        
    def atest_placementOrder(self):
        
        part1 = self.createPart(self.root_pa, "above")
        part1 = self.root_service.addStickyContent(self.t_name, 
                                                   part1,
                                                   self.slotname)
        part2 = self.createPart(self.root_pa2, "above")
        part2 = self.root_service.addStickyContent(self.t_name, 
                                                   part2,
                                                   self.slotname)
        parts = list(self.root_service.getStickyContentForLayoutSlot(
            self.t_name, self.slotname))
        self.assertEquals([part1,part2], parts)

        #now change the placement of part1, it should now be below part2
        ad = IStickySupport(part1)
        ad.changePlacement("below")
        parts = list(self.root_service.getStickyContentForLayoutSlot(
            self.t_name, self.slotname))
        self.assertEquals([part2,part1], parts)
        
    def atest_getStickyContent(self):
        #test for getting sticky content by it's layout and partkey.
        #this will attempt to acquire the sticky content if it does not
        # exist in the local service
        
        part1 = self.createPart(self.root_pa)
        part1 = self.root_service.addStickyContent(self.t_name, 
                                                   part1,
                                                   self.slotname)
        part2 = self.createPart(self.pub1_pa)
        part2 = self.pub1_service.addStickyContent(self.t_name, 
                                                   part2,
                                                   self.slotname)
        
        #test without acquiring
        sp = self.pub1_service.getStickyContent(self.t_name,
                                                part2.getKey(),
                                                acquire=False)
        self.assertEquals(part2,sp)
        
        #test with acquiring, but get local sticky content
        sp = self.pub1_service.getStickyContent(self.t_name,
                                                part2.getKey(),
                                                acquire=True)
        self.assertEquals(part2,sp)
        
        #test acquiring
        sp = self.pub1_service.getStickyContent(self.t_name,
                                                part1.getKey(),
                                                acquire=True)
        self.assertEquals(part1,sp)
        
        #test an invalid key
        sp = self.pub1_service.getStickyContent(self.t_name,
                                                1234,
                                                acquire=True)
        self.assertEquals(None,sp)
        

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StickyContentServiceTestCase))
    return suite

