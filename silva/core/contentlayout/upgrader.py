import logging

from zope.component import getUtility
import transaction

from Acquisition import aq_base

from silva.core.interfaces import ISilvaObject, IVersionedContent
from silva.core.upgrade.upgrade import BaseUpgrader, content_path

logger = logging.getLogger('silva.core.contentlayout')

VERSION_B1 = '2.3b1'
VERSION_FINAL='2.3.0'

class ContentLayoutServiceRenamer(BaseUpgrader):
    
    def upgrade(self, root):
        #rename service, if the old name is present
        if hasattr(root, 'service_content_templates'):
            #rename doesn't work, so attempt a manual recreate
#            root.manage_renameObject('service_content_templates',
#                                      'service_contentlayout')
            from silva.core.contentlayout.services import \
                 manage_addContentLayoutService
            manage_addContentLayoutService(root, 'service_contentlayout')
            scl = root.service_contentlayout
            sct = root.service_content_templates
            for o in ('_content_template_mapping','_default_non_cl'):
                scl.__dict__[o] = getattr(sct, o)
            root.manage_delObjects(['service_content_templates'])
        return root
            
renamer = ContentLayoutServiceRenamer('2.2.22', 'Silva Root')

class ContentLayoutServiceUpgrader(BaseUpgrader):
    
    def upgrade(self, root):
        #content storage has changed, update it
        obj = getattr(root, 'service_contentlayout', None)
        if not obj:
            return root
        if hasattr(obj, '_content_template_mapping'):
            obj._template_mapping = obj._content_template_mapping
            del obj._content_template_mapping
        if hasattr(obj, '_default_non_cl'):
            del obj._default_non_cl
        for key,val in obj._template_mapping.iteritems():
            #change allowed to a set
            if val.has_key('allowed'):
                val['allowed'] = set(val['allowed'])
        return root
#register this on the root rather than the obj, since this needs to be updated
# BEFORE the SNN 2.8 upgrade (registered on Silva 2.2b1)
cls_upgrader = ContentLayoutServiceUpgrader('2.2.23', 
                                            'Silva Root')

