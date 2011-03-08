from ContentLayoutTestCase import ContentLayoutTestCase
from zExceptions import BadRequest
from Products.Silva.contentlayout.parts import ExternalSourcePart

class PageAssetTestCase(ContentLayoutTestCase):
    
    def afterSetUp(self):
        super(PageAssetTestCase, self).afterSetUp()
        #copy an external source into the root
        self.installExtension("SilvaExternalSources")
        self.login('manager')
        token = self.root.service_codesources.manage_copyObjects(["cs_multitoc"])
        self.root.manage_pasteObjects(token)
        self.login('chiefeditor') 
        self.cs_name = "cs_multitoc"
        
    def test_save_name(self):
        #test setting the name of an external source within the page asset
        p = self.root_pa
        e = p.get_editable()
        
        e.setName(self.cs_name)
        #the name should exist (as the cs was copied to the root)
        self.assertEquals(self.cs_name, e.getName())
        self.assertRaises(BadRequest, e.setName, 'blah')
        
    def test_save_config(self):
        #test saving the config, and getting it back
        p = self.root_pa
        e = p.get_editable()
        config = {'paths':'pub1'}
        e.setName(self.cs_name)
        e.setConfig(config)
        self.assertEquals(config, e.getConfig())
        self.assertRaises(TypeError, e.setConfig, None)

    def test_NotImplementedMethods(self):
        #These should all raise a NotImplementedError

        p = self.root_pa
        e = p.get_editable()
        config = {'paths': 'pub'}
        e.setName(self.cs_name)
        e.setConfig(config)
        self.assertRaises(NotImplementedError, e.update_quota) 
        self.assertRaises(NotImplementedError, e.reset_quota)
        self.assertRaises(NotImplementedError, e.get_filename)
        self.assertRaises(NotImplementedError, e.get_file_size) 
        self.assertRaises(NotImplementedError, e.get_mime_type)

        
import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PageAssetTestCase))
    return suite
