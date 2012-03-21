from zope.component import getMultiAdapter
from zope.interface import alsoProvides
from zope.publisher.browser import TestRequest

from silva.core.interfaces import ISiteManager
from Products.Silva.testing import smi_settings

from ContentLayoutTestCase import ContentLayoutTestCase


class StickyContentServiceFuncTestCase(ContentLayoutTestCase):
    
    def setUp(self):
        super(StickyContentServiceFuncTestCase, self).setUp()
        #the root service is added during Silva install
        self.root_service = self.root.service_sticky_content
        
        #make pub1 a local site so it can contain a sticky content service
        ISiteManager(self.pub1).makeSite()
        self.pub1.manage_addProduct['silva.core.contentlayout'].manage_addStickyContentService()
        self.pub1_service = self.pub1.service_sticky_content
        
        self.t_name = "silva.core.contentlayout.templates.OneColumn"
        self.slotname = 'maincontent'
        
        self.login('chiefeditor')
        
    def test_stickybutton_exists(self):
        #verify the sticky button exists in the middleground for
        # IPublications
        sb = self.layer.get_browser(smi_settings)
        sb.login('chiefeditor')

        sb.open('/root/edit/tab_metadata')
        self.assertEquals(sb.get_link('sticky').url, 'http://localhost/root/edit/tab_sticky_content')
        
        sb.open('/root/pub/edit/tab_metadata')
        self.assertEquals(sb.get_link('sticky').url, 'http://localhost/root/pub/edit/tab_sticky_content')
        

    #def test_addremove_sticky(self):
        #sb = self.layer.get_browser(smi_settings)
        #sb.options.handle_errors = False
        #sb.login('chiefeditor')
        #cformname = 'form.addstickycontentsubform'
        #create = cformname + '.action.create'
        #rformname = 'form.removestickycontentsubform'
        #remove = rformname + '.action.remove'
        
        #sb.open('/root/pub2/edit/tab_sticky_content')
        #form = sb.get_form(cformname)
        #self.assertTrue(create in form.controls)
        ##remove form should not be present on the page
        #self.assertRaises(AssertionError, sb.get_form, rformname)
        #form.get_control(create).click()
        #self.assertEquals(sb.status_code, 200)
        #self.assertTrue(ISiteManager(self.pub2).isSite())
        
        #form = sb.get_form(rformname)
        #self.assertTrue(remove in form.controls)
        ##create form should not be present on the page
        #self.assertRaises(AssertionError, sb.get_form, cformname)
        #form.get_control(remove).click()
        #self.assertEquals(sb.status_code, 200)
        #self.assertFalse(ISiteManager(self.pub2).isSite())
        
    #def test_manage_presence(self):
        ##check presence of the manage sticky content subform
        ## -- it should be present on an IPub with a service
        ##    and be absent on an IPub with no service
        #sb = self.layer.get_browser(smi_settings)
        #sb.login('chiefeditor')
        #formname = 'form.managestickycontentsubform'
        #sb.inspect.add('mform', '//form[@name="%s"]'%formname)
        #sb.options.handle_errors = False
        
        ##pub has a sticky service, so edit form should exist
        #sb.open('/root/pub/edit/tab_sticky_content')
        #self.assertTrue(len(sb.inspect.mform)==1)
        
        ##pub2 does not have a sticky service, so edit form should not exist
        #sb.open('/root/pub2/edit/tab_sticky_content')
        #self.assertTrue(len(sb.inspect.mform)==0)

        
        
import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StickyContentServiceFuncTestCase))
    return suite

