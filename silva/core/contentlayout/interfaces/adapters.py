from zope.interface import Interface

from zope.interface import Interface

class IRichTextCleanup(Interface):
    
    def from_editor(self, text):
        """convert html coming in from the editor (i.e. being
           validated) into html suitable for storage (e.g.
           "storage html".  I.E. convert paths (using IPathAdapter)"""
    
    def to_editor(self, text):
        """convert html from "storage html" to that which is suitable
           for editing.  Note: this may be the same as to_public"""
    
    def to_public(self, text):
        """convert "storage html" to that which is suitable for
           public viewing.  Convert paths (IPathAdapter), update
           silva image info (width, height, title, strip ?webform)
           and possibly other things.  In the future (Silva 2.3)
           this will convert references into urls"""
        
        
__all__ = ["IRichTextCleanup"]

