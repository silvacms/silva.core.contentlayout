import logging

from zope.component import getUtility
import transaction

from Acquisition import aq_base

from silva.core.interfaces import ISilvaObject, IVersionedContent
from silva.core.upgrade.upgrade import BaseUpgrader, content_path

logger = logging.getLogger('silva.core.contentlayout')

VERSION_FINAL='2.3'

class ContentLayoutServiceUpgrader(BaseUpgrader):
    
    def upgrade(self, obj):
        #content storage has changed, update it
        if hasattr(self, '_content_template_mapping'):
            self._template_mapping = self._content_template_mapping
            del self._content_template_mapping
        for key,val in self._template_mapping.iteritems():
            #change allowed to a set
            if val.has_key('allowed'):
                val['allowed'] = set(val['allowed'])

cls_upgrader = ContentLayoutServiceUpgrader(VERSION_FINAL, 
                                            'Silva Content Layout Service')

class RootUpgrader(BaseUpgrader):
    def upgrade(self, root):
        #need to remove some views things here
        pass
root_upgrader = RootUpgrader(VERSION_FINAL,
                             'Silva Root')
