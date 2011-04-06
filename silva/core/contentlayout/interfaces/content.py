from zope.interface import Interface

class IRichTextExternalSource(Interface):
    """ marker interface for the "rich text" external source, manually add
        this to that external source"""
    
__all__ = ["IRichTextExternalSource"]

