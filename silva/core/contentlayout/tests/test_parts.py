from ContentLayoutTestCase import ContentLayoutTestCase
from zExceptions import NotFound
from Products.Silva.contentlayout.parts import ExternalSourcePart
from Products.Silva.contentlayout.interfaces import IPartFactory

class PartsTestCase(ContentLayoutTestCase):
    
    def afterSetUp(self):
        super(PartsTestCase, self).afterSetUp()
        #copy two external sources into the root
        self.installExtension("SilvaExternalSources")
        self.login('manager')
        token = self.root.service_codesources.manage_copyObjects(["cs_multitoc"])      
        self.root.manage_pasteObjects(token)
        token = self.root.service_codesources.manage_copyObjects(["cs_rich_text"])
        self.root.manage_pasteObjects(token)
        token = self.root.service_codesources.manage_copyObjects(["cs_page_asset"])
        self.root.manage_pasteObjects(token)
        self.login('chiefeditor')
        
    def test_ExternalSourcePart(self):    
        cs = getattr(self.root, 'cs_multitoc')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        # Make sure getters for part work correctly
        self.assertEquals(part._name, part.getName())
        self.assertEquals(part._config, part.getConfig())
        self.assertEquals(part._key, part.getKey())
        part.setConfig({'paths':'pub2'})
        # Make sure configuration was correctly updated
        self.assertEquals(part.getConfig(), {'paths':'pub2'})


    def test_RichTextPart(self):
        cs = getattr(self.root, 'cs_rich_text')
        factory = IPartFactory(cs)
        part = factory.create({'paths':'pub'})
        self.assertEquals(part._name, part.getName())
        self.assertEquals(part._config, part.getConfig())
        self.assertEquals(part._key, part.getKey())
        part.setConfig({'paths':'pub2'})
        self.assertEquals(part.getConfig(), {'paths':'pub2'})


import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PartsTestCase))
    return suite
