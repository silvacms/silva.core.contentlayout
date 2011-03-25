import copy

from five import grok
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.traversing.interfaces import ITraversable
from zope.interface import alsoProvides
from zope.component import getUtility, getMultiAdapter
from zExceptions import BadRequest

from Products.Formulator.Errors import FormValidationError
from Products.SilvaExternalSources import ExternalSource
from Products.SilvaExternalSources.interfaces import (IExternalSource,
                                                      ICodeSource)
from silva.core.interfaces.adapters import IVersionManagement
from silva.core.views import views as silvaviews
from silva.core.views.traverser import UseParentByAcquisition
from silva.core.views.interfaces import ILayoutEditorLayer
from silva.core.smi.interfaces import ISMILayer
from silva.core.layout.porto import porto
from silva.core.interfaces import (IVersionedContentLayout,
                                   IContentLayout)
from silva.core.contentlayout.interfaces import (IContentLayoutService,
                                                 ITitleEditWidget,
                                                 ITitleView,
                                                 IPartEditWidget,
                                                 IPartViewWidget,
                                                 IPartView,
                                                 IPartFactory)

class EditorTraversable(grok.MultiAdapter):
    """Traverser to the layout editor layer -- converts a content layout
       content-type's public view to the layout editor view.
       
       Adds the layer to the request if needed
    """
    grok.adapts(IContentLayout, IBrowserRequest)
    grok.implements(ITraversable)
    grok.name('layouteditor')
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def traverse(self, name, remaining):
        if not ILayoutEditorLayer.providedBy(self.request):
            alsoProvides(self.request, ILayoutEditorLayer)
        return UseParentByAcquisition()

class VersionedEditorTraversable(EditorTraversable):
    """so that this traverser can be used on the content objects, and not
       just the versions"""
    grok.adapts(IVersionedContentLayout, IBrowserRequest)

class LayoutEditHeaders(silvaviews.Viewlet):
    """defines a viewlet to add layout editor code to the html head of
       the content layout public rendering"""
    grok.viewletmanager(porto.HTMLHeadInsert)
    grok.layer(ILayoutEditorLayer)

class PropertiesPreviewProvider(silvaviews.ContentProvider):
    """defines a content provider which provides "properties"-related
       content for the layout editor, to be displayed in the content layout
       template ONLY when in preview mode"""

class LayoutEditTab(grok.View):
    grok.context(IContentLayout)
    grok.require("silva.ReadSilvaContent")
    
    def default_namespace(self):
        ns = super(LayoutEditTab, self).default_namespace()
        editable = self.context.get_editable()
        sct = getUtility(IContentLayoutService)
        layout_name = editable.get_layout_name()

        ns['editable'] = editable
        ns['layout_name'] = layout_name
        ns['layout_template'] = sct.get_template_by_name(layout_name)
        ns['sct'] = sct
        
        mt = editable.get_content().meta_type
        allowed = sct.get_allowed_templates(mt)
        templates = [ c for c in allowed if 
                      c[0] != layout_name ]
        ns['templates'] = templates
        return ns
    
    def get_external_source_list(self):
        """Return an ordered list of the External Sources within the
           current context.  Each item is a three-tuple of 
           [ priority, title, name, source ]"""
        sources = [ [s[1].priority(),s[1].title.encode('utf-8'),s[0], s[1]] \
                    for s in ExternalSource.availableSources(self.context.aq_inner) ]
        sources.sort()
        return sources

    def render_external_source_icon(self, source):
        """Render an External Source's icon.  If it is a codesource, it attempts
           to get the sources unique icon, otherwise the meta type's icon
           is used"""
        if ICodeSource.providedBy(source) and source.get_icon() and \
           source.get_icon().meta_type=="Image":
            icon = source.get_icon()
            return icon.tag()
        else:
            #XXX this is in ViewCode(?)
            return self.context.render_icon(source)

class EditDialogIFrame(grok.View):
    """get full page edit dialog for placing within an iframe
    """
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    
    def render_dialog(self):
        """retrieve the actual edit dialog, render it"""
        dialog = getMultiAdapter((self.context, self.request),
                                 name="edit-dialog")
        return dialog(self.parttype, self.esname, self.mode, self.slotname,
                      self.partkey)
        
    def __call__(self, parttype, esname=None, mode='edit', slotname=None, 
                 partkey=None):
        self.parttype = parttype
        self.esname = esname
        self.mode = mode
        self.slotname=slotname
        self.partkey = partkey
        return super(EditDialogIFrame, self).__call__()

def _get_source(context, esname):
    """helper function to get the ExternalSource `esname`
       within the current context"""
    try:
        source = getattr(context.aq_inner,esname)
    except AttributeError:
        raise BadRequest, 'Invalid external source name'
    except TypeError:
        raise BadRequest, 'esname must be a string'
    if not IExternalSource.providedBy(source):
        raise BadRequest, 'Invalid external source'
    return source

class EditDialog(grok.View):
    """the edit dialog for the ExternalSource `esname`.  Returns the
       IPartEditWidget for the source.

       If mode=='add', then return the edit view without values pre-filled.
       If mode=='edit', lookup the part identified by `partkey` in the
         slot `slotname`, and send that part's config to the edit view.
         the edit view will be rendered using that part's config.
    """
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.name("edit-dialog")

    def update(self):
        if self.partkey:
            self.partkey = int(self.partkey)

    def render(self):
        #XXX having `model` available in the request is required for some
        # formulator fields (e.g. lookupwindowfield)
        #fix the model, so it is the ISilvaObject
        self.request.set('model', self.context.aq_inner.get_content())
        
        if self.parttype=="page-title":
            ad = getMultiAdapter((self.context, self.request),
                                 interface=ITitleEditWidget)
            return ad()
        elif self.parttype=="es":
            source = _get_source(self.context, self.esname)
            ad = getMultiAdapter((source, self.request), 
                                 interface=IPartEditWidget)
            config = None
            if self.mode=='edit':
                #if editing, get the part and values, which will then be
                # set in the form
                part = self.context.get_part(self.partkey)
                config = copy.deepcopy(part.get_config())
            return ad(contentlayout=self.context,
                      mode=self.mode,
                      slotname=self.slotname,
                      partkey=self.partkey,
                      partconfig=config,
                      suppressFormTag=False)

    def __call__(self, parttype, esname=None, mode='edit', slotname=None, 
                 partkey=None):
        self.parttype = parttype
        self.esname = esname
        self.mode = mode
        self.slotname=slotname
        self.partkey = partkey
        return super(EditDialog, self).__call__()
    
class SavePart(grok.View):
    """View for saving parts.  I imagine that at some point this will
       change into a zeam.form (alongside or part of the editdialog.
       External Sources will also need to move into zeam forms before this
       can happen"""
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")
    parttype = None
    partkey = None
    
    def update(self):
        if self.request.form.has_key('partkey'):
            self.partkey = int(self.request.form['partkey'])
    
    def render(self):
        if self.parttype=='page-title':
            title = self.request['pagetitle']
            self.context.set_title(title)
            #return the new content for "inside" the view widget
            ad = getMultiAdapter((self.context, self.request),
                                 interface=ITitleView)
            return ad()
        elif self.parttype=='es':
            """given the partkey, get the part, validate the form results
               (against the parts external source), saving the result
               into the parts' config.

               Return the rendered source using the IPartView
               interface"""
            part = self.context.get_part(self.partkey)
            if not part:
                raise BadRequest, 'invalid part key'

            try:
                ad = getMultiAdapter((self.context, self.request),
                                     name='validateeditdialog')
                result = ad(parttype='es', esname=part.get_name(), 
                            returnResult=True)
            except FormValidationError:
                raise BadRequest, 'es form validation error'
            
            #replace part's config with the result
            part.set_config(result)
            self.context.sec_update_last_author_info() 
            ad = getMultiAdapter((part, self.request), 
                                 interface=IPartView)
            ad.slot = self.context.get_slot_name_for_part(part)
            ad.contentlayout = self.context
            ad.checkPreviewable = True
            return ad()
        
    def __call__(self, parttype):
        self.parttype = parttype
        return super(SavePart, self).__call__()
    
class AddPartToSlot(grok.View):
    """Validate the result to the ExternalSource `esname`.
       create a new IPart with the result,
       add it to the slot before the part with key `beforepartkey`.
       if `beforepartkey` is None, then add it to the end.

       Return the rendered rendered using the IPartViewWidget
       interface
    """
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")
    def render(self):
        if not self.slotname:
            raise BadRequest, 'slotname must be specified'
        try:
            ad = getMultiAdapter((self.context, self.request),
                                 name='validateeditdialog')
            result = ad(parttype='es', esname=self.esname, returnResult=True)
        except FormValidationError:
            raise BadRequest, 'es form validation error'

        source = _get_source(self.context, self.esname)
        #use a factory to create the IPart, so that different
        # external sources can have different Parts.
        factory = IPartFactory(source)
        part = factory.create(result)

        if self.beforepartkey:
            self.beforepartkey = int(self.beforepartkey)
        else:
            #explicitly set before 
            self.beforepartkey = None
        part = self.context.add_part_to_slot(part, self.slotname, 
                                             self.beforepartkey)
        self.context.sec_update_last_author_info()
        ad = getMultiAdapter((part, self.request),
                             interface=IPartViewWidget)
        ad.slot = self.slotname
        ad.contentlayout = self.context
        return ad()
    
    def __call__(self, esname, slotname, beforepartkey=None):
        self.esname = esname
        self.slotname = slotname
        self.beforepartkey = beforepartkey
        return super(AddPartToSlot, self).__call__()

class ValidateEditDialog(grok.View):
    """Validate the form data for a part."""
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")
    
    def render(self):
        """get the rendered form
           This code is based on ES.get_rendered_form_for_editor

           @returnResult: when true the result dictionary is returned on success
                          Otherwise the string "Success" is returned
            The former is useful to calling from code, the latter
            useful for AJAX validation
            In the event of a validation error, the error is raised when
            returnResult is true, otherwise the error is converted to a 
            string and a 400 "Bad Request" response is returned.
           """
        if self.parttype=='page-title':
            #XXX we probably need some sort of validation here...
            return "Success"
        elif self.parttype=='es':
            source = _get_source(self.context, self.esname)
            form = source.get_parameters_form()
            try:
                result = form.validate_all(self.request)
            except FormValidationError, e:
                if not self.returnResult: 
                    #coming in from an AJAX request, respond by sending error
                    #messages back
                    self.request.RESPONSE.setStatus(400, 'Bad Request')
                    return '&'.join(['%s=%s' % (e.field['title'], e.error_text) 
                                     for e in e.errors])
                else:
                    raise e
            if self.returnResult:
                return result
            return "Success"
        else:
            raise BadRequest, 'parttype must be specified'
        
    def __call__(self, parttype, esname=None, returnResult=False):
        self.parttype = parttype
        self.esname= esname
        self.returnResult = returnResult
        return super(ValidateEditDialog, self).__call__()
    
class AddablesScreen(grok.View):
    """ get the addables screen, which is a pretty (and larger) format
       rendering of the common addables (external sources)
    """
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")

    def get_external_source_list(self):
        """Return an ordered list of the External Sources within the
           current context.  Each item is a three-tuple of 
           [ priority, title, name, source ]"""
        sources = [ [s[1].priority(),s[1].title.encode('utf-8'),s[0], s[1]] \
                    for s in ExternalSource.availableSources(self.context.aq_inner) ]
        sources.sort()
        return sources
    
    def update(self):
        #get the common (i.e. priority==1) external sources
        self.common_sources = [ s for s in self.get_external_source_list()
                                if s[0] < 10 ]
        self.common_sources.sort();

class RemovePart(grok.View):
    """Remove the part identified by `partkey` from slot `slotname`"""
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")

    def render(self):
        """remove the part"""
        try:
            partkey = int(self.partkey)
            self.context.remove_part(partkey)
        except:
            raise BadRequest, 'invalid partkey'
        self.context.sec_update_last_author_info()
        return "OK" #return something so as to avoid HTTP 204 buggy
                     #behavior in IE browsers
    
    def __call__(self, partkey):
        self.partkey =  partkey
        return super(RemovePart, self).__call__()

class MovePartToSlot(grok.View):
    """Move the part identified by `partkey` from the slot
       it is currently in to the slot identified by `slotname`
    """
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")

    def update(self):
        try:
            self.partkey = int(self.partkey)
        except:
            raise BadRequest, 'invalid partkey'
        if self.beforepartkey:
            try:
                self.beforepartkey = int(self.beforepartkey)
            except:
                raise BadRequest, 'invalid partkey'
        else:
            #explicitly make it none, in case "beforepartkey=" was sent in the
            #request, which makes it ''
            self.beforepartkey = None

    def render(self):
        try:
            self.context.move_part_to_slot(self.partkey, 
                                           self.slotname, 
                                           self.beforepartkey)
        except:
            raise BadRequest, 'invalid partkey or beforepartkey'
        self.context.sec_update_last_author_info()
        #return something so as to avoid HTTP 204 buggy
        #behavior in IE browsers
        return "OK" 

    def __call__(self, partkey, slotname, beforepartkey=None):
        self.partkey =  partkey
        self.slotname = slotname
        self.beforepartkey = beforepartkey
        return super(MovePartToSlot, self).__call__()

class SwitchLayoutTemplate(grok.View):
    """Switch the content layout's template to a new template."""
    grok.layer(ISMILayer)
    grok.context(IContentLayout)
    grok.require("silva.ChangeSilvaContent")

    def render(self):
        #XXX create a new version of the content here
        #close editable version, create a new version and switch the
        # template in that version
        version_ad = IVersionManagement(self.context.aq_inner.get_content())
        version_ad.revertPreviousToEditable(version_ad.getUnapprovedVersion().id)
        self.context = version_ad.getUnapprovedVersion()
        self.context.switch_template(self.newTemplate)
        self.context.sec_update_last_author_info()
        return "OK"

    def __call__(self, newTemplate):
        self.newTemplate = newTemplate
        return super(SwitchLayoutTemplate, self).__call__()

pass #for better code folding support, leave this at the bottom of the module