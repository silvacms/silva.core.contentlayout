from Testing import ZopeTestCase
from Products.Silva.tests import SilvaTestCase
from AccessControl.SecurityManagement import newSecurityManager
import transaction

#silva
from Products.Silva.testing import TestCase
import layer

import silva.core.contentlayout

class ContentLayoutTestCase(TestCase):
    
    layer = layer.ContentLayoutLayer(silva.core.contentlayout,
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
        return self.addObject(object, 'Page', id, title=title,
                              product='silva.app.page')
    
    def add_page_asset(self, object, id, title):
        return self.addObject(object, 'PageAsset', id, title=title,
                              product='silva.app.page')
        
    def login(self, username):
        uf = self.layer.get_application().acl_users
        user = uf.getUserById(username).__of__(uf)
        newSecurityManager(None, user)

    def setUp(self):
        super(ContentLayoutTestCase, self).setUp()
        self.root = self.layer.get_application()
        self.service = self.root.service_contentlayout
        self.pub1 = self.add_publication(self.root, 'pub', "Publication")
