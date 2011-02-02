from zope.interface import Interface

class IVersionedContentLayout(Interface):
    """Marker interface for VersionedContent objects wich
       store versiones supporting content layout
    """

class IContentLayout(Interface):
    """An interface to support complex content layouts.
       NOTE: for versionedcontent, the versions provide this interface
    """
    
    def add_part_to_slot(part, slot):
        """@part(IContentLayoutPart)
           @slot - name of a slot
           add the part to the slot with the given mane.
           May or may not require validation that the slot name
           is valid for the current layout
        """
    
    def get_parts_for_slot(slot):
        """@slot - name of a slot for the current layout
           returns the list of parts in the specified slot
        """

__all__ = ['IVersionedContentLayout','IContentLayout']