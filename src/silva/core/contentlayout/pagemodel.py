# -*- coding: utf-8 -*-
# (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.component import getMultiAdapter
from zope.i18n import translate

from AccessControl import ClassSecurityInfo
from AccessControl.security import checkPermission
from App.class_init import InitializeClass

from zeam.form import silva as silvaforms
from silva.core import conf as silvaconf
from silva.core.smi.content import IEditScreen
from silva.core.interfaces.events import IContentPublishedEvent
from silva.core.interfaces.events import IContentClosedEvent
from silva.ui.interfaces import IJSView
from silva.ui.rest.base import Screen, PageREST
from silva.core.views.interfaces import ISilvaURL
from silva.core.views import views as silvaviews
from silva.translations import translate as _
from Products.Silva.VersionedContent import VersionedContent
from Products.Silva.Version import Version

from .interfaces import IPageModel, IPageModelVersion, PageModelFields
from .interfaces import IContentLayoutService, IDesign
from .designs.design import DesignAccessors


class PageModelVersion(Version, DesignAccessors):
    """ A version of a Silva Page Model
    """
    grok.implements(IPageModelVersion)
    security = ClassSecurityInfo()
    meta_type = 'Silva Page Model Version'

    _description = None
    _title = None
    _allowed_content_types = None

    def get_identifier(self):
        return getUtility(IIntIds).register(self.get_content())

    def set_title(self, title):
        self._title = title

    def get_title(self):
        return self._title or ''

    def get_allowed_content_types(self):
        return self._allowed_content_types

    def set_allowed_content_types(self, types):
        self._allowed_content_types = set(types)
        return self._allowed_content_types

    @property
    def markers(self):
        design = self.get_design()
        if design is not None:
            return design.markers
        return []

    def get_slots(self):
        pass

    def set_slots(self):
        pass

    def get_description(self):
        return self._description

    def set_description(self, value):
        self._description = value

    def __call__(self, content, request):
        return PageModelRender(self, content, request)


InitializeClass(PageModelVersion)


class PageModel(VersionedContent):
    """ A Silva Page Model is content type that represents a template
    where you can add slots / default blocks and restrictions.
    """
    grok.implements(IPageModel)
    silvaconf.version_class(PageModelVersion)
    silvaconf.priority(-20)

    meta_type = 'Silva Page Model'
    security = ClassSecurityInfo()


InitializeClass(PageModel)


class PageModelRender(object):
    grok.implements(IDesign)

    def __init__(self, model, content, request):
        self.model = model
        self.content = content
        self.request = request

    def __call__(self, edition=None):
        __info__ = 'Rendering model: %s' % self.model
        design = self.model.get_design()
        render = design(self.model, self.request)
        return render(edition=edition)


class PageModelAddForm(silvaforms.SMIAddForm):
    """ Add form for page models.
    """
    grok.name(PageModel.meta_type)
    fields = PageModelFields


class PageModelEdit(PageREST):
    grok.adapts(Screen, IPageModel)
    grok.name('content')
    grok.implements(IEditScreen)
    grok.require('silva.ReadSilvaContent')

    def payload(self):
        if checkPermission('silva.ChangeSilvaContent', self.context):
            version = self.context.get_editable()
            if version is not None:
                view = getMultiAdapter(
                    (version, self.request), IJSView, name='content-layout')
                return view(self, identifier=version.getId())

        url = getMultiAdapter((self.context, self.request), ISilvaURL).preview()
        return {"ifaces": ["preview"],
                "html_url": url}


class PageModelView(silvaviews.View):
    grok.context(IPageModel)

    def render(self):
        msg = _('Sorry, this ${meta_type} is not viewable.',
                mapping={'meta_type': self.context.meta_type})
        return '<p>%s</p>' % translate(msg, context=self.request)


@grok.subscribe(IPageModelVersion, IContentPublishedEvent)
def register(version, event):
    service = getUtility(IContentLayoutService)
    service.register_page_model(version)


@grok.subscribe(IPageModelVersion, IContentClosedEvent)
def unregister(version, event):
    service = getUtility(IContentLayoutService)
    service.unregister_page_model(version)
