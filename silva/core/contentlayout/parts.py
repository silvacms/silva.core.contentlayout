import pickle
import time
import random
import sys

from five import grok
from zope.component import getMultiAdapter, getUtility

from persistent.mapping import PersistentMapping
from Acquisition import aq_inner, aq_acquire

from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from Products.Silva import SilvaPermissions
from Products.SilvaExternalSources.interfaces import IExternalSource
from Products.SilvaExternalSources.ExternalSource import ExternalSource
from silva.core.interfaces import IContentLayout

from silva.core.contentlayout.interfaces import (IPart, IExternalSourcePart, 
                                                 IPartFactory, IPartEditWidget,
                                                 IRichTextPart,
                                                 IRichTextExternalSource,
                                                 IPartView, IPartViewWidget,
                                                 ITitleView, ITitleViewWidget,
                                                 ITitleEditWidget,
                                                 IContentLayoutService,
                                                 IStickySupport)

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
    
    
class BasePartView(grok.View):
    """ base class mixin for adapters which render the view of
        content layout parts
    """
    
    grok.implements(IPartView)
    #all part views should are views which provide IPartView, so they
    # can all be looked up by interface (NO name)
    grok.provides(IPartView)
    grok.name('')
    grok.baseclass()
    contentlayout = None
    checkPreviewable = False
    slot = None
    contentlayout = None
    wrapClass = None
    
    
class ExternalSourcePartView(BasePartView):
    """Part View Widget for external sources.
    """
    grok.context(IExternalSourcePart)
    grok.name('')

    def render(self):
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
            source = aq_acquire(context, self.context.get_name())
            #don't allow the keyword args specifically for this adapter
            # to bleed into the external source view code.
            if self.checkPreviewable and not source.is_previewable():
                ret = "<div class='not-previewable'>This content, a '%s', is not previewable.</div>"%source.get_title()
            else:
                config = self.context.get_config(copy=True)
                ret = source.to_html(content=self.context,
                                     request=self.request, 
                                     **config)
            if self.wrapClass:
                return '<div class="%s">%s</div>'%(self.wrapClass, ret)
            else:
                return ret
        except Exception, e:
            url = self.context.aq_acquire("error_log").raising( sys.exc_info() )
            return """<div class="warning"><strong>[""" + \
                   "content part is broken" + \
                  "]</strong><br />error message: " + str(e) + \
                   "<br />Check the error log for more information.</div>"

        
class PartViewWidget(grok.View):
    """Renders the preview of an IContentLayoutPart
        as a widget for the layout template's
        edit screen (in the smi)"""
    grok.context(IPart)
    grok.implements(IPartViewWidget)
    grok.provides(IPartViewWidget)
    grok.name(u'')
    slot = None
    contentlayout = None
    wrapClass = None
    
    def render_part(self, interface=IPartView):
        """given the IPart part (self.context),
           render it using it's IPartView, or an alternate interface passed
           in via the `interface` parameter.
        """
        ad = getMultiAdapter((self.context, self.request), 
                             interface=interface)
        ad.slot = self.slot
        ad.contentlayout = self.contentlayout
        ad.wrapClass = self.wrapClass
        ad.checkPreviewable=True
        return ad()

    
class BasePartEditWidget(grok.View):
    """ base class mixin for adapters which render the edit view of 
        content layout parts (allowing authors to change
        the IPart
    """
    grok.implements(IPartEditWidget)
    #all part edit widgets are unnamed views which provide IPartEditWidget,
    # so they can all be looked up by interface (NO name)
    grok.provides(IPartEditWidget)
    grok.name('')
    grok.baseclass()
    #the content layout object associated with this part
    content_layout = None

    
class ExternalSourcePartEditWidget(BasePartEditWidget):
    """Part Edit Widget for External Sources.
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
    
    
class TitleView(BasePartView):
    grok.implements(ITitleView)
    grok.provides(ITitleView)
    grok.context(IContentLayout)
    grok.name(u'')
    
    def render_title(self):
        """get the title heading level from the content template
           generate the title html by hand, since each template may have
           a different heading level
        """
        sct = getUtility(IContentLayoutService)
        layout_name = self.context.get_layout_name()
        template = sct.get_template_by_name(layout_name)
        level = template.title_heading_level
        title = self.context.get_title()
        extra = self.request.get('title-extra',None)
        if extra:
            title += ' ' + extra
        return '<h%s class="page-title">%s</h%s>'%(level, title, level)
    
    def render(self):
        return self.render_title()

    
class TitleViewWidget(grok.View):
    """Wraps the TitleView inside HTML to make the title an editable
       widget in the layout editor.
    """
    grok.implements(ITitleViewWidget)
    grok.provides(ITitleViewWidget)
    grok.context(IContentLayout)
    grok.name(u'')
    
    def render_part(self):
        """Render the `part` (the title)"""
        return getMultiAdapter((self.context, self.request),
                               interface=ITitleView)()

    
class TitleEditWidget(BasePartEditWidget):
    grok.implements(ITitleEditWidget)
    grok.provides(ITitleEditWidget)
    grok.context(IContentLayout)
    grok.name('')

    
class StickySupport(grok.Adapter):
    """class to get sticky settings (above, below, possibly others)
    out of an ISupportsSticky part (which should only be the
    cs_page_asset, but could possibly include others"""
    grok.context(IExternalSourcePart)
    grok.implements(IStickySupport)
    
    def __init__(self, part):
        self.part = part
        
    def get_placement(self):
        """Get the placement (either above or below)
           for a sticky content part.  This assumes
           the part has a config param 'placement', which
           stores the string 'above' or 'below'.  If not,
           the placement is below"""
        c = self.part.get_config()
        if c.has_key('placement'):
            if c['placement'] == 'above':
                return 'above'
        return 'below'
    
    def change_placement(self, newplacement):
        """newplacement is either 'above' or 'below'.
           If the part has a config param 'placement',
           this updates the value of that configparam to
           `newplacement`"""
        c = self.part.get_config()
        if newplacement=='above':
            c['placement'] = 'above'
        else:
            c['placement'] = 'below'