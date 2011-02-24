import pickle
import time
import random
import sys

from five import grok

from persistent.mapping import PersistentMapping
from Acquisition import aq_inner, aq_acquire

from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.Silva import SilvaPermissions
from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaExternalSources.ExternalSource import ExternalSource

from silva.core.contentlayout.interfaces import (IExternalSourcePart, 
                                                 IPartFactory, IPartEditWidget,
                                                 IContentLayout, IRichTextPart,
                                                 IRichTextExternalSource,
                                                 IPartView)

class ExternalSourcePart(SimpleItem):
    """An ExternalSourcePart represents a "part" in a content layout slot
       which is defined by the settings for the specified external source.
       The rendered part should be simply the rendered external source.
    """

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
        
    security.declareProtected(SilvaPermissions.ChangeSilvaContent, "set_config")
    def set_config(self, config):
        self._config = config
        
    security.declareProtected(SilvaPermissions.ReadSilvaContent, "get_name")
    def get_name(self):
        return self._name
        
    security.declareProtected(SilvaPermissions.ReadSilvaContent, "get_config")
    def get_config(self, copy=False):
        if copy:
            return dict(self._config)
        return self._config
    
    security.declareProtected(SilvaPermissions.ReadSilvaContent, "get_key")
    def get_key(self):
        return self._key
    
InitializeClass(ExternalSourcePart)

class RichTextPart(ExternalSourcePart):
    grok.implements(IRichTextPart)
    meta_type = "Rich Text Part"
    security = ClassSecurityInfo()

    def __str__(self):
        return "RichTextPart(%s): %s"%(self._name, self._config)
InitializeClass(RichTextPart)

class PartFactory(grok.Adapter):
    """The base class for factories which create a specific type of part"""
    
    grok.baseclass()
    grok.provides(IPartFactory)
    def __init__(self, source):
        self.source = source
        
    def create(self, result):
        raise NotImplemented, "the create method is implemented in subclasses"

class ExternalSourcePartFactory(PartFactory):
    grok.context(IExternalSource)
    def create(self, result):
        """Actually create an ExternalSourcePart for the result (which is the
           validated results dictionary for an external source
        """
        return ExternalSourcePart(self.source.id, result)
    
class RichTextPartFactory(PartFactory):
    grok.context(IRichTextExternalSource)
    def create(self, result):
        return RichTextPart(self.source.id, result)
    
class BasePartView(object):
    """ base class mixin for adapters which render the view of
        content layout parts
    """
    
    grok.implements(IPartView)
    grok.name('part-view')
    grok.baseclass()
    
class ExternalSourcePartView(BasePartView, grok.View):
    """Part View Widget for external sources.
       XXX see note below (edit widget) for new feature request
    """
    grok.context(IExternalSourcePart)

    def render(self, *args, **kw):
        """The public view for an external source part.  Two parameters may
           be passed in to configure the output of this view:
           1) checkPreviewable [boolean] : if True, will check whether this
              external source is previewable.  If not, will output some std
              'not previewable' language.
            2) wrapClass [string] : if set, the rendered source will have a div
               with class=wrapClass wrapped around it.
        """
        #slot and content_layout are parameters in the interface contract, but
        #are ignore in this implementation.  They are in the contract
        # to more easily support view switching with ContentLayoutPartViewWidget
        try:
            context = aq_inner(self.context)
            source = aq_acquire(context, self.context.get_part_name())
            #don't allow the keyword args specifically for this adapter
            # to bleed into the external source view code.
            wrapClass = ''
            if kw.has_key('wrapClass'):
                wrapClass = kw['wrapClass']
                del kw['wrapClass']
            checkPreviewable = False
            if kw.has_key('checkPreviewable'):
                checkPreviewable = kw['checkPreviewable']
                del kw['checkPreviewable']
            
            if checkPreviewable and not source.is_previewable():
                ret = "<div class='not-previewable'>This content, a '%s', is not previewable.</div>"%source.get_title()
            else:
                config = self.context.get_config(copy=True)
                ret = source.to_html(content=self.context,
                                     request=self.request, 
                                     **config)
            if wrapClass:
                return '<div class="%s">%s</div>'%(wrapClass, ret)
            else:
                return ret
        except Exception, e:
            url = self.context.aq_acquire("error_log").raising( sys.exc_info() )
            return """<div class="warning"><strong>[""" + \
                   "content part is broken" + \
                  "]</strong><br />error message: " + str(e) + \
                   "<br />Check the error log for more information.</div>"

class BasePartEditWidget(object):
    """ base class mixin for adapters which render the edit view of 
        content layout parts (allowing authors to change
        the IPart
    """
    grok.implements(IPartEditWidget)
    grok.name('part-edit-widget')

class ExternalSourcePartEditWidget(BasePartEditWidget, grok.View):
    """Part Edit Widget for External Sources.
       XXX it would be nice if this could be a "view" adapter on 
       IExternalSource,IContentLayout...
       Unfortunately, grok.View's only provide Interface, so they
       cannot be looked up by interface.  Instead they need to be
       looked up by their name. (found in grokcore.views.meta.view)
    """
    grok.context(IExternalSource)
    grok.require('silva.ChangeSilvaContent')
    
    def default_namespace(self):
        """Since grok stupidly (ha!) doesn't by default pass parameters
           to the template (via calling the template with a list of params), 
           they aren't by default accessible through 'options' (it is always
           empty).  So override it here
        """
        ns = super(ExternalSourcePartEditWidget,self).default_namespace()
        ns['options'] = self.options
        ns['contentlayout'] = self.contentlayout
        return ns
    
    def __call__(self, contentlayout, mode='add', slotname=None, partkey=None, 
                 partconfig=None, submitButtonName=None, from_request=False,
                 suppressFormTag=True, submitOnTop=False):
        """Call the edit widget. ``self.context`` is an IExternalSource,
           self.contentlayout is the model containing the part (this could be
           an IContentLayout or an IPageAsset.
        """
           
        if partkey:
            partkey = int(partkey)
        self.contentlayout = contentlayout
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