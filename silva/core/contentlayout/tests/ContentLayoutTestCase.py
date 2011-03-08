from Testing import ZopeTestCase
from Products.Silva.tests import SilvaTestCase
import transaction

#silva
from Products.Silva.testing import TestCase, SilvaLayer

import silva.core.contentlayout

class ContentLayoutTestCase(TestCase):
    
    layer = SilvaLayer(silva.core.contentlayout,
                       zcml_file='configure.zcml')
    
    def addObject(self, container, type_name, id, product='Silva', **kw):
        getattr(container.manage_addProduct[product],
                'manage_add%s' % type_name)(id, **kw)
        # gives the new object a _p_jar ...
        transaction.savepoint()
        return getattr(container, id)
    
    def add_publication(self, object, id, title, **kw):
        return self.addObject(object, 'Publication', id, title=title, **kw)
    
    def add_page(self, object, id, title):
        return self.addObject(object, 'Page', id, title=title)
    
    def add_page_asset(self, object, id, title):
        return self.addObject(object, 'PageAsset', id, title=title)
        
    def setUp(self):
        self.pub1 = self.add_publication(self.root, 'pub', "Publication")
        self.page = self.add_page(self.pub1, "page", "Page")
        self.root_pa = self.add_page_asset(self.pub1, "root_pa", "Page Asset")
        self.root_pa2 = self.add_page_asset(self.pub1, "root_pa2", "Page Asset 2")
        self.pub1_pa = self.add_page_asset(self.pub1, "pub1_pa", "Page Asset")
