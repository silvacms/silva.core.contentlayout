from ContentLayoutTestCase import ContentLayoutTestCase
from zExceptions import NotFound
from Products.Silva.contentlayout.parts import ExternalSourcePart
from Products.Silva.contentlayout.interfaces import  IPartFactory
from DateTime import DateTime

class VersionedAssetTestCase(ContentLayoutTestCase):
    
    def afterSetUp(self):
        super(VersionedAssetTestCase, self).afterSetUp()
      
    def test_publicationStuff(self):
        # root_pa should not be published or approved at this point
        assert(not self.root_pa.is_published())
        assert(not self.root_pa.is_approved())
        assert(self.root_pa.get_viewable() is None)
        #Editable and previewable version should be identicle
        self.assertEquals(self.root_pa.get_editable(), self.root_pa.get_previewable())
        #Test setting and getting title
        assert(self.root_pa.can_set_title())
        self.assertEquals('Page Asset', self.root_pa.get_title_editable())
        self.root_pa.set_title('Title')
        self.assertEquals('Title', self.root_pa.get_title_editable())
        self.assertEquals('root_pa', self.root_pa.get_title())
        # Make sure that for an unpublished version get_title returns ID
        self.root_pa.set_unapproved_version_publication_datetime(DateTime())
        self.root_pa.approve_version()
        # Make sure root_pa was published correctly
        self.assertEquals('Title', self.root_pa.get_title())
        assert(self.root_pa.get_viewable() is not None)
        self.assertEquals(self.root_pa.get_viewable(), self.root_pa.get_previewable())
        assert(self.root_pa.is_published())



        print self.root_pa.get_content()


     
        # Create new editable version
        self.root_pa.create_copy()
        # Test title and defaults for nav and short title
        self.root_pa.set_title('')
        self.assertEquals('root_pa', self.root_pa.get_title_or_id_editable())
        self.root_pa.set_title('Test')
        self.assertEquals('Test', self.root_pa.get_title_or_id_editable())
        self.assertEquals('Title', self.root_pa.get_short_title())
        self.assertEquals('Test', self.root_pa.get_short_title_editable())
        self.assertEquals('Title', self.root_pa.get_nav_title())
        self.assertEquals('Test', self.root_pa.get_nav_title_editable())
        assert(self.root_pa.get_editable() is not None)
        # Publish root_pa again and test
        self.root_pa.set_unapproved_version_publication_datetime(DateTime())
        self.root_pa.approve_version()
        assert(self.root_pa.get_editable() is None)
        assert(self.root_pa.get_last_closed() is not None)
        assert(self.root_pa.is_published())
        
        #Test approval of root_pa
        assert(not self.root_pa.is_approved())
        self.root_pa.create_copy()
        #This code will break after Y3K
        self.root_pa.set_unapproved_version_publication_datetime(DateTime('3000/1/1 00:00:00'))
        self.root_pa.approve_version()
        assert(self.root_pa.is_approved())

        # Is not deletable?
        assert(not self.root_pa.is_deletable())
        self.assertEquals(self.root_pa.indexVersions(), None)

        self.assertEquals(self.root_pa.unindexVersions(), None)
        # Test CatalogedVersionedAsset when there is code using it.
        
import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(VersionedAssetTestCase))
    return suite
