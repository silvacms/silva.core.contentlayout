from zope.component.interfaces import ComponentLookupError

from ContentLayoutTestCase import ContentLayoutTestCase

class ContentLayoutServiceTestCase(ContentLayoutTestCase):
    
    def setUp(self):
        super(ContentLayoutServiceTestCase, self).setUp()
        self.one = 'silva.core.contentlayout.templates.OneColumn'
        self.two = 'silva.core.contentlayout.templates.TwoColumn'
   
    def test_registerTemplates(self):
        self.service.set_allowed_templates('Silva Page', set((self.one, self.two)))
        self.service.set_default_template('Silva Page', self.one)
        
        self.assertEquals(set((self.one, self.two)), 
                          set(self.service.get_allowed_template_names('Silva Page')))
        
        self.assertEquals(self.one, self.service.get_default_template('Silva Page'))
        #reset type back to default, check default behavior
        self.service.set_default_template('Silva Page', None)
        self.service.set_allowed_templates('Silva Page', set())

        #Test registerTemplates with no default or allowed templates
        check = list(self.service.get_allowed_templates('Silva Page'))
        self.assertEquals([t for t in self.service.get_sorted_templates()], 
                          check)
        self.assertEquals([t[0] for t in self.service.get_sorted_templates()], 
                          list(self.service.get_allowed_template_names('Silva Page')))
        self.assertEquals(None, self.service.get_default_template('Silva Page'))
         
    def test_getTemplateByName(self):
        #Basic tests for get_template_by_name
        self.assertEquals('One Column (standard)', self.service.get_template_by_name(self.one).name)
        self.assertEquals('Two Column (standard)', self.service.get_template_by_name(self.two).name)
        #Make sure the appropriate error is raised for non-existent template name
        self.assertRaises(ComponentLookupError, self.service.get_template_by_name, 'String')

    def test_getSortedTemplates(self):
        st = []
        t = []

        for i in self.service.get_sorted_templates():
            i = list(i)
            if i[0] in [self.one, self.two]:
                st.append(i)

        self.assertEquals(len(st), 2)
        
import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContentLayoutServiceTestCase))
    return suite
