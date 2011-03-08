import os

from ContentLayoutTestCase import ContentLayoutTestCase
from Products.Silva.silvaxml import xmlimport

def testopen(path, rw):
    directory = os.path.dirname(__file__)
    return open(os.path.join(directory, path), rw)

class XMLImportTestCase(ContentLayoutTestCase):

    def afterSetUp(self):
        super(XMLImportTestCase, self).afterSetUp()
        #copy external source into the root
        self.installExtension("SilvaExternalSources")
        self.login('manager')
        token = self.root.service_codesources.manage_copyObjects(["cs_rich_text"])
        self.root.manage_pasteObjects(token)
        token = self.root.service_codesources.manage_copyObjects(["cs_page_asset"])
        self.root.manage_pasteObjects(token)
        self.login('chiefeditor')

    def test_page_import(self):
        source = testopen('data/test_pages.xml', 'r')
        xmlimport.importFromFile(source, self.root)
        source.close()

        pub = self.root.page_import
        assert(pub)
        self.assertEquals('Page Import', pub.get_title())

        p1 = pub.p1
        assert(p1)
        self.assertEquals('p1', p1.get_title())
        assert(not p1.get_viewable())
        e = p1.get_editable()
        assert(e)
        self.assertEquals('Page 1', p1.get_title_editable())
        self.assertEquals('silva.contentlayouttemplates.onecolumn', e.getLayoutName())
        parts = list(e.getPartsForSlot('maincontent'))
        self.assertEquals(1, len(parts))
        self.assertEquals('cs_rich_text', parts[0].getName())
        self.assertEquals({'rich_text': '<p>Test</p>'}, parts[0].getConfig())

        p2 = pub.p2
        assert(p2)
        self.assertEquals('p2', p2.get_title())
        assert(not p2.get_viewable())
        e = p2.get_editable()
        assert(e)
        self.assertEquals('Page 2', p2.get_title_editable())
        self.assertEquals('silva.contentlayouttemplates.onecolumn', e.getLayoutName())
        parts = list(e.getPartsForSlot('maincontent'))
        self.assertEquals(0, len(parts))

        p3 = pub.p3
        assert(p3)
        self.assertEquals('Page 3', p3.get_title())
        assert(not p3.get_editable())
        v = p3.get_viewable()
        assert(v)
        self.assertEquals('silva.contentlayouttemplates.onecolumn', v.getLayoutName())
        parts = list(v.getPartsForSlot('maincontent'))
        self.assertEquals(2, len(parts))
        self.assertEquals('cs_rich_text', parts[0].getName())
        self.assertEquals({'rich_text': '<p>Hello world</p>'}, parts[0].getConfig())
        self.assertEquals('cs_page_asset', parts[1].getName())
        self.assertEquals({'placement': 'above', 'object_path': 'pa'}, parts[1].getConfig())

    def test_page_asset_import(self):
        source = testopen('data/test_pageassets.xml', 'r')
        xmlimport.importFromFile(source, self.root)
        source.close()

        pub = self.root.page_asset_import
        assert(pub)
        self.assertEquals('Page Asset Import', pub.get_title())

        pa1 = pub.pa1
        assert(pa1)
        self.assertEquals('pa1', pa1.get_title())
        assert(not pa1.get_viewable())
        e = pa1.get_editable()
        assert(e)
        self.assertEquals('Page Asset 1', pa1.get_title_editable())
        self.assertEquals('cs_rich_text', e.getName())
        self.assertEquals({'rich_text': '<p><strong>July</strong> <em>20</em>, <span style="text-decoration: underline;">1969</span></p>'}, e.getConfig())

        pa2 = pub.pa2
        assert(pa2)
        self.assertEquals('pa2', pa2.get_title())
        assert(not pa2.get_viewable())
        e = pa2.get_editable()
        assert(e)
        self.assertEquals('Page Asset 2', pa2.get_title_editable())
        self.assertEquals('cs_rich_text', e.getName())
        self.assertEquals({}, e.getConfig())

        pa3 = pub.pa3
        assert(pa3)
        self.assertEquals('Page Asset 3', pa3.get_title())
        assert(pa3.get_viewable())
        assert(not pa3.get_editable())
        self.assertEquals('cs_rich_text', pa3.get_viewable().getName())
        self.assertEquals({'rich_text': '<p>This is a test!</p>'}, pa3.get_viewable().getConfig())

import unittest
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(XMLImportTestCase))
    return suite
