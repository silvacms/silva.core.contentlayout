from Testing import ZopeTestCase
from Products.Silva.contentlayout.parts import ExternalSourcePart
from Products.Silva.tests.SilvaTestCase import SilvaFunctionalTestCase
from Products.Silva.tests.SilvaBrowser import SilvaBrowser
import re

ZopeTestCase.installProduct('SiteErrorLog')

class ContentLayoutFunctionalTest(SilvaFunctionalTestCase):
    
    def afterSetUp(self):
        super(ContentLayoutFunctionalTest, self).afterSetUp()
        #copy an external source into the root
        self.installExtension("SilvaExternalSources")
        self.login('manager')
        token = self.root.service_codesources.manage_copyObjects(["cs_multitoc"])
        self.root.manage_pasteObjects(token)
        token = self.root.service_codesources.manage_copyObjects(["cs_rich_text"])
        self.root.manage_pasteObjects(token)
        self.login('chiefeditor') 
        self.cs_name = "cs_multitoc"
        self.root.manage_addProduct["SiteErrorLog"].manage_addErrorLog()
        self.log = getattr(self.root, "error_log")
     
    def test_silvaPageAjaxCalls(self):
        sb = SilvaBrowser()
        sb.login('manager', 'secret', sb.smi_url())
        sb.make_content('Silva Page', id = 'test_page', title = 'test')
        status, url = sb.go('../test_page/edit')

        
        status, url = sb.go('0/tab_edit_cl_switch_template', 'newTemplate=silva.contentlayouttemplates.twocolumn')
       
        #Make sure the default templates are in the drop down  
        sb.go('http://nohost/root/test_page/edit')
        
        p = re.compile('<a class="yuimenuitemlabel"\n\s*value="(silva.*)">\n\s*<span class="template-name">(.*)</span>')
        
        s = p.search(sb.browser.contents)
        
        # The page is using silva.contentlayouttempaltes.twocolum right now, so .onecolumn should be in the drop down
        self.assertEquals('silva.contentlayouttemplates.onecolumn', s.group(1))
        self.assertEquals('One Column', s.group(2))
        
        #Switch to the other template do the same
        status, url = sb.go('0/tab_edit_cl_switch_template', 'newTemplate=silva.contentlayouttemplates.onecolumn')
        sb.go('http://nohost/root/test_page/edit')
        
        p = re.compile('<a class="yuimenuitemlabel"\n\s*value="(silva.*)">\n\s*<span class="template-name">(.*)</span>')
        
        s = p.search(sb.browser.contents)

        # now the page is on .onecolumn, so .twocolumn should be in the drop down
        self.assertEquals('silva.contentlayouttemplates.twocolumn', s.group(1))
        self.assertEquals('Two Column', s.group(2))
        
        status, url = sb.go('0/tab_edit_cl_switch_template', 'newTemplate=silva.contentlayouttemplates.twocolumn')
        sb.go('http://nohost/root/test_page/edit')
        
        #Add an ES to the page
        
        #Change Title
   
        #Test bad part type
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=pe-title&pagetitle=Test')
        self.assertEquals(400, status)
        
        #Part type only mattered for the first 'status, url = ...'

        #Actually change it
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=page-title&pagetitle=Test')
        self.assertEquals(200, status)
        self.assertEquals('Success', sb.browser.contents)
        status, url = sb.go('0/tab_edit_cl_save_part', 'parttype=page-title&pagetitle=Test')
        self.assertEquals(200, status)
        self.assertEquals('<h3 class="page-title">Test</h3>', sb.browser.contents)

        #First, test validation
        status, url = sb.go('0/tab_edit_cl_switch_template', 'newTemplate=silva.contentlayouttemplates.twocolumn')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)
        
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=feature&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(200, status)
        self.assertEquals('Success', sb.browser.contents)

        #Test invalid esname
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=feature&esname=cs_rich_tex&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing parttype
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=&slotname=feature&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing parttype
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'slotname=feature&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing slotname (not used during validation)
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(200, status)
        self.assertEquals('Success', sb.browser.contents)
        
        #Test missing slotname (not used during validation)
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(200, status)
        self.assertEquals('Success', sb.browser.contents)

        #Test missing esname
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=feature&esname=&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing esname
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=feature&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing field_rich_text
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=feature&esname=cs_rich_text&field_rich_text=')
        self.assertEquals(400, status)
        
        #Test missing field_rich_text
        status, url = sb.go('0/tab_edit_cl_validate_edit_dialog', 'parttype=es&slotname=feature&esname=cs_rich_text')
        self.assertEquals(400, status)
        
        #Second, test adding it
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(200, status)
        
        #We need to grab the partkey for later use
        p = re.compile('<div class="part" id="cs_rich_text_(-?\d+)">')
        s = p.search(sb.browser.contents)
        self.partkey = s.group(1)
                
        #Test invalid esname
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&esname=cs_rich_tex&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing slotname
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing slotname
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing esname
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&esname=&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing esname
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing field_rich_text
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&esname=cs_rich_text&field_rich_text=')
        self.assertEquals(400, status)
        
        #Test missing field_rich_text
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&esname=cs_rich_text')
        self.assertEquals(400, status)

        #Third, edit it
        status, url = sb.go('0/@@tab_edit_cl_save_part', 'parttype=es&slotname=feature&partkey=' + self.partkey + '&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(200, status)
        self.assertEquals('<p>hi</p>', sb.browser.contents)
        
        #Test invalid partkey
        status, url = sb.go('0/@@tab_edit_cl_save_part', 'parttype=es&slotname=feature&partkey=0123456789&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        
        #Test missing partkey
        status, url = sb.go('0/@@tab_edit_cl_save_part', 'parttype=es&slotname=feature&partkey=&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)
        #Test missing partkey

        status, url = sb.go('0/@@tab_edit_cl_save_part', 'parttype=es&slotname=feature&esname=cs_rich_text&field_rich_text=%3Cp%3Ehi%3C%2Fp%3E')
        self.assertEquals(400, status)

        
        #Fourth, move it

        #Test invalid partkey                                                                                                                                                   
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=123456&slotname=panel')
        self.assertEquals(400, status)
        
        #Test missing partkey
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'slotname=panel&partkey=')
        self.assertEquals(400, status)
        
        #Test missing partkey
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'slotname=panel')
        self.assertEquals(400, status)
        
        # Testing for invalid slotname doesn't work because the slot is created if the name doesn't exist
        # status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkey + '&slotname=fake')
        # self.assertEquals(400, status)
        
        #Test missing slotname
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'slotname=&partkey=' + self.partkey)
        self.assertEquals(400, status)
        
        #Test missing slotname
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkey)
        self.assertEquals(400, status)
        
        #Actually move it
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkey + '&slotname=panel')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)


        #Next, delete it
        
        #Test invalid partkey
        status, url = sb.go('0/@@tab_edit_cl_remove_part', 'partkey=0123456789')
        self.assertEquals(400, status)
        
        #Test missing partkey
        status, url = sb.go('0/@@tab_edit_cl_remove_part', 'partkey=')
        self.assertEquals(400, status)
        
        #Test missing partkey
        status, url = sb.go('0/@@tab_edit_cl_remove_part', '')
        self.assertEquals(400, status)

        #Actually delete it
        status, url = sb.go('0/@@tab_edit_cl_remove_part', 'partkey=' + self.partkey)
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)

        #Finally, test with more than one part

        #part one
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=panel&esname=cs_rich_text&field_rich_text=%3Cp%3Epart1%3C%2Fp%3E')
        self.assertEquals(200, status)
        
        #Grab the key
        p = re.compile('<div class="part" id="cs_rich_text_(-?\d+)">')
        s = p.search(sb.browser.contents)
        self.partkeyone = s.group(1)

        #part two
        status, url = sb.go('0/@@tab_edit_cl_add_es_to_slot', 'parttype=es&slotname=feature&esname=cs_rich_text&field_rich_text=%3Cp%3Epart2%3C%2Fp%3E')
        self.assertEquals(200, status)
        
        #Grab this key as well  
        p = re.compile('<div class="part" id="cs_rich_text_(-?\d+)">')
        s = p.search(sb.browser.contents)
        self.partkeytwo = s.group(1)
        #Move part one to the same slot as part two
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkeyone + '&slotname=feature')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)

        #Move it back
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkeyone + '&slotname=panel')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)

        #Move part two to the same one
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkeytwo + '&slotname=panel')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)

        #Move part one to the other slot 
        status, url = sb.go('0/tab_edit_cl_move_part_to_slot', 'partkey=' + self.partkeyone + '&slotname=feature')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)

        #Switch to other template
        status, url = sb.go('0/tab_edit_cl_switch_template', 'newTemplate=silva.contentlayouttemplates.onecolumn')
        self.assertEquals(200, status)
        self.assertEquals('OK', sb.browser.contents)
        

    def test_addSilvaPage(self):
        sb = SilvaBrowser()
        status, url = sb.login('manager', 'secret', sb.smi_url())
        addables = sb.get_addables_list()
        self.failUnless('Silva Page' in addables)
        sb.select_addable('Silva Page')
        # create silva document                                                                                              
        status, url = sb.click_button_labeled('new...')
        self.failUnless(sb.get_addform_title() == 'create Silva Page')
        # fill in form fields                                                                                                
        sb.set_id_field('test_content')
        sb.set_title_field('test content')
        status, url = sb.click_button_labeled('save')
        self.failUnless(sb.get_status_feedback().startswith('Added Silva Page'))


    def test_addSilvaPageAsset(self): 
        sb = SilvaBrowser()
        status,url = sb.login('manager', 'secret', sb.smi_url())
        addables = sb.get_addables_list()
        self.failUnless('Silva Page Asset' in addables)
        sb.select_addable('Silva Page Asset')
        # create silva document
        status, url = sb.click_button_labeled('new...')
        self.failUnless(sb.get_addform_title() == 'create Silva Page Asset')
        # fill in form fields
        sb.set_id_field('test_content')
        sb.set_title_field('test content')
        status, url = sb.click_button_labeled('save')
        self.failUnless(sb.get_status_feedback().startswith('Added Silva Page Asset'))

    def test_pageAssetAjaxCalls(self):
        sb = SilvaBrowser()
        sb.login('manager', 'secret', sb.smi_url())
        sb.make_content('Silva Page Asset', id = 'test_page', title = 'Test')
        status, url = sb.go('../test_page/edit')

        #Add an ES to the page

        #Bad extsource name
        status, url = sb.go('http://nohost/root/test_page/edit/', 'extsource=cs_rch_text&change-es%3Amethod=change+external+source')
        self.assertEquals(400, status)
        
        #Empty extsource name
        status, url = sb.go('http://nohost/root/test_page/edit/', 'extsource=&change-es%3Amethod=change+external+source')
        self.failUnless(sb.get_alert_feedback().startswith('An external source must be selected'))

        #No extsource name
        status, url = sb.go('http://nohost/root/test_page/edit/', 'change-es%3Amethod=change+external+source')
        self.assertEquals(400, status)
        
        #Now actually add it
        status, url = sb.go('http://nohost/root/test_page/edit/', 'extsource=cs_rich_text&change-es%3Amethod=change+external+source')
        self.assertEquals(200, status)

        #Change External Source
        status, url = sb.go('http://nohost/root/test_page/edit/', 'extsource=cs_rich_text&change-es%3Amethod=change+external+source&parttype=es&slotname=a&partkey=12345&esname=cs_rich_text&field_rich_text=')
        self.assertEquals(200, status)
    
        #The parameters that were not tested do not impact the call
        
import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContentLayoutFunctionalTest))
    return suite
