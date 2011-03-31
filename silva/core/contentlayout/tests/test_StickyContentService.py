from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

from silva.core.interfaces import ISiteManager
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

    def test_StickyServiceExists(self):
        #simple test to make sure the service was added to each container
        self.assertEquals(True, 
                          hasattr(self.root, 'service_sticky_content'))
        self.assertEquals(True, 
                          hasattr(self.pub1, 'service_sticky_content'))
        
        

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StickyContentServiceTestCase))
    return suite

