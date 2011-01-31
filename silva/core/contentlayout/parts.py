import pickle
import time
import random

from five import grok

from persistent.mapping import PersistentMapping

from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from Globals import InitializeClass

from Products.Silva import SilvaPermissions
from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaExternalSources.ExternalSource import ExternalSource

from interfaces import (IExternalSourcePart, IPartFactory, IPartEditWidget,
                        IContentLayout)

class ExternalSourcePart(SimpleItem):
    meta_type = "External Source Part"
    grok.implements(IExternalSourcePart)
    security = ClassSecurityInfo()
    
    def __init__(self, name, config):
        #this is the name of the external source
        self._name = name
        self._config = PersistentMapping(config)
        #this key is used by the content layout to uniquely identify
        # the part.  The part can then be referenced by this key, rather than
        # (or in addition to) it's index within the slot (which will change)
        self._key = hash(pickle.dumps(config) + \
                         repr(self) + \
                         str(time.time()) + \
                         str(random.randint(-1000000,1000000)))
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent, "setConfig")
    def setConfig(self, config):
        self._config = config
        
    security.declareProtected(SilvaPermissions.ReadSilvaContent, "getName")
    def getName(self):
        return self._name
        
    security.declareProtected(SilvaPermissions.ReadSilvaContent, "getConfig")
    def getConfig(self, copy=False):
        if copy:
            return dict(self._config)
        return self._config
    
    security.declareProtected(SilvaPermissions.ReadSilvaContent, "getKey")
    def getKey(self):
        return self._key
    
InitializeClass(ExternalSourcePart)

class PartFactory(grok.Adapter):
    grok.baseclass()
    grok.provides(IPartFactory)
    def __init__(self, source):
        self.source = source
        
    def create(self, result):
        raise NotImplemented, "the create method is implemented in subclasses"

class ExternalSourcePartFactory(PartFactory):
    grok.context(IExternalSource)
    def create(self, result):
        "Actually create an external source part for the source"
        return ExternalSourcePart(self.source.id, result)
    
class BasePartEditWidget(object):
    grok.implements(IPartEditWidget)
    grok.name('part-edit-widget')

class ExternalSourcePartEditWidget(BasePartEditWidget, grok.View):
    """Part Edit Widget for External Sources.
       XXX it would be nice if this could be a "view" adapter on 
       IExternalSource,IContentLayout...
       Unfortunately, grok.View's only provide Interface, so they
       cannot be looked up by interface.  Instead they need to be
       looked up by their name. (found in grokcore.views.meta.view)"""
    grok.context(IExternalSource)
    grok.require('silva.ChangeSilvaContent')
    
    def default_namespace(self):
        """Since grok stupidly (ha!) doesn't by default pass parameters
        to the template (via calling the template with a list of params), 
        they aren't by default accessible through 'options' (it is always
        empty).  So override it here"""
        ns = super(ExternalSourcePartEditWidget,self).default_namespace()
        ns['options'] = self.options
        ns['content'] = self.content
        return ns
    
    def __call__(self, content, mode='add', slotname=None, partkey=None, 
                 partconfig=None, submitButtonName=None, from_request=False,
                 suppressFormTag=True, submitOnTop=False):
        if partkey:
            partkey = int(partkey)
        self.content = content
        self.options = {
            'mode':mode,
            'slotname':slotname,
            'partkey':partkey,
            'partconfig':partconfig,
            'submitButtonName':submitButtonName,
            'from_request':from_request,
            'suppressFormTag':suppressFormTag,
            'submitOnTop':submitOnTop
            }
        return super(ExternalSourcePartEditWidget,self).__call__()