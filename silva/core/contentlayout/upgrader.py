import logging

from zope.component import getUtility
import transaction

from Acquisition import aq_base

from silva.core.interfaces import ISilvaObject, IVersionedContent
from silva.core.upgrade.upgrade import BaseUpgrader, content_path

logger = logging.getLogger('silva.core.contentlayout')

VERSION_B1 = '2.3b1'
VERSION_FINAL='2.3'

class ContentLayoutServiceRenamer(BaseUpgrader):
    
    def upgrade(self, root):
        #rename service, if the old name is present
        if hasattr(root, 'service_content_templates'):
            root.manage_renameObject('service_content_templates',
                                      'service_contentlayout')
        return root
            
#renamer = ContentLayoutServiceRenamer(VERSION_B1, 'Silva Root')
renamer = ContentLayoutServiceRenamer('2.3.1b1', 'Silva Root')

class ContentLayoutServiceUpgrader(BaseUpgrader):
    
    def upgrade(self, obj):
        #content storage has changed, update it
        if hasattr(obj, '_content_template_mapping'):
            obj._template_mapping = obj._content_template_mapping
            del obj._content_template_mapping
        if hasattr(obj, '_default_non_cl'):
            del obj._default_non_cl
        for key,val in obj._template_mapping.iteritems():
            #change allowed to a set
            if val.has_key('allowed'):
                val['allowed'] = set(val['allowed'])
        return obj

cls_upgrader = ContentLayoutServiceUpgrader(VERSION_FINAL, 
                                            'Silva Content Layout Service')

