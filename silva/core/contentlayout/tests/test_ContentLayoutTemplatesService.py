from ContentLayoutTestCase import ContentLayoutTestCase
from zope.component.interfaces import ComponentLookupError


class ContentLayoutTemplatesServiceTestCase(ContentLayoutTestCase):
    
    def afterSetUp(self):
        super(ContentLayoutTemplatesServiceTestCase, self).afterSetUp()
        self.s = self.root.service_content_templates
        self.one = 'silva.contentlayouttemplates.onecolumn'
        self.two = 'silva.contentlayouttemplates.twocolumn'
   
    def test_registerTemplates(self):
        self.s.registerTemplates('Silva Page', {'default': self.one, 'allowed': [self.one, self.two]})
        #Make sure registerTemplates worked correctly
        self.assertEquals([self.one, self.two], self.s.getAllowedTemplatesForMetaType('Silva Page'))
       
        self.s.registerTemplates('Silva Page', {'default': None, 'allowed': []})
        #Test registerTemplates with no default or allowed templates
        self.assertEquals([t[0] for t in self.s.getTemplateTuples()], self.s.getAllowedTemplatesForMetaType('Silva Page'))      
        self.assertEquals(None, self.s.getDefaultTemplateForMetaType('Silva Page'))
    
    def test_supportsContentLayout(self):
        #Basic tests for supportsContentLayout
        self.assertEquals(True, self.s.supportsContentLayout('Silva Page'))
        self.assertEquals(False, self.s.supportsContentLayout('Silva File'))
        self.assertEquals(False, self.s.supportsContentLayout('Silva Image'))
        #Testing for a non-existent meta-type
        self.assertEquals(False, self.s.supportsContentLayout('asdfsd'))
        
    def test_getSupportingMetaTypes(self):
        # Might need to adjust if additional products like Silva News are installed in these test cases
        self.assertEquals(['Silva Page'], self.s.getSupportingMetaTypes())
        
        

    def test_getTemplateByName(self):
        #Basic tests for getTemplateByName
        self.assertEquals('One Column', self.s.getTemplateByName(self.one).getName())
        self.assertEquals('Two Column', self.s.getTemplateByName(self.two).getName())
        #Make sure the appropriate error is raised for non-existent template name
        self.assertRaises(ComponentLookupError, self.s.getTemplateByName, 'String')


    def test_getSortedTemplates(self):
        st = []
        t = []

        for i in self.s.getSortedTemplates():
            i = list(i)
            if i[0] in [self.one, self.two]:
                st.append(i)

        self.assertEquals(len(st), 2)

    def test_getFormulatorTemplateTuples(self):
        # Since there may be other templates in addition to the two basic ones in contentlayout, 
        # this section only tests those two and ignores any others
        self.s.registerTemplates('Silva Page', {'default': self.one, 'allowed': [self.one, self.two]})
        # getFormulatorTemplateTuples for an invalid meta-type should return all templates which will number at least two
        assert(len(list(self.s.getFormulatorTemplateTuples('sdfsd'))) >= len(list(self.s.getFormulatorTemplateTuples('Silva Page'))))
        # For no specificied meta-type we should get same result.
        assert(len(list(self.s.getFormulatorTemplateTuples())) >= len(list(self.s.getFormulatorTemplateTuples('Silva Page'))))
        ft = self.s.getFormulatorTemplateTuples('Silva Page')
        tt = list(self.s.getTemplateTuples())
        t = list(self.s.getTemplates())
        tt_final = []
        t_final = []
        # Convert generators to lists and save results for two basic templates
        for i in tt:
            i = list(i)
            if i[0] in [self.one, self.two]:
                tt_final.append(i)
        for i in t:
            i = list(i)
            if i[0] in [self.one, self.two]:
                t_final.append(i)
        # These should now be the same length
        self.assertEquals(len(ft), len(tt_final))
        self.assertEquals(len(tt_final), len(t_final))
        
        # For each item in array, make sure it is for one of the two base templates and has appropriate values
        for i in ft:
            i = list(i)
            if i[1] == self.one:
                # Make sure template name is the same
                self.assertEquals('One Column', i[0])
            elif i[1] == self.two:
                self.assertEquals('Two Column', i[0])
            else:
                self.fail()
                
        for i in tt_final:
            if i[0] == self.one:
                self.assertEquals('One Column', i[1])
                #Make sure the description is the same
                self.assertEquals('a simple one column layout', i[2])
            elif i[0] == self.two:
                self.assertEquals('Two Column', i[1])
                self.assertEquals('a simple two column layout', i[2])
            else:
                self.fail()

        for i in t_final:
            if i[0] == self.one:
                self.assertEquals('One Column', i[1].getName())
            elif i[0] == self.two:
                self.assertEquals('Two Column', i[1].getName())
            else:
                self.fail()
        
import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContentLayoutTemplatesServiceTestCase))
    return suite
