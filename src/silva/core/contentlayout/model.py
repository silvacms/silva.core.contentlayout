# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt
# (c) 2012 Infrae. All rights reserved.

import operator

from five import grok
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.component import getMultiAdapter
from zope.i18n import translate

from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.interfaces import IObjectWillBeRemovedEvent
from OFS.Folder import Folder

from silva.core import conf as silvaconf
from silva.core.interfaces import IRoot
from silva.core.interfaces.events import IContentClosedEvent
from silva.core.interfaces.events import IContentPublishedEvent
from silva.core.interfaces.events import IContentImported
from silva.core.views import views as silvaviews
from silva.core.smi.settings import Settings
from silva.translations import translate as _
from silva.ui.interfaces import IJSView
from silva.ui.menu import ExpendableMenuItem, ContentMenu
from silva.ui.rest.base import Screen, PageREST
from silva.ui.rest.container.listing import ContainerListing
from zeam.form import silva as silvaforms

from Products.Silva.VersionedContent import VersionedObject
from Products.Silva.Version import Version
from Products.Silva import SilvaPermissions

from .interfaces import IPageModel, IPageModelVersion, PageModelFields
from .interfaces import IContentLayoutService, IBlockSlot, IBlockManager
from .designs.design import DesignAccessors
from silva.core.contentlayout.interfaces import IDesignAssociatedEvent, IPage,\
    IDesignDeassociatedEvent
from silva.core.references.interfaces import IReferenceService


class PageModelVersion(Version, DesignAccessors):
    """ A version of a Silva Page Model
    """
    grok.implements(IPageModelVersion)
    security = ClassSecurityInfo()
    meta_type = 'Silva Page Model Version'

    _allowed_content_types = None
    _role = None

    security.declareProtected(
        SilvaPermissions.View, 'get_design_title')
    def get_design_title(self):
        # Return Silva title as design title.
        return self.get_title()

    security.declareProtected(
        SilvaPermissions.View, 'get_design_identifier')
    def get_design_identifier(self):
        # Return the IntID of the model as identifier.
        return getUtility(IIntIds).register(self.get_silva_object())

    security.declareProtected(
        SilvaPermissions.View, 'get_all_design_identifiers')
    def get_all_design_identifiers(self, known=None):
        # We have to build this method passing a list as argument, in
        # order to prevent infinite recursion if there is a loop in
        # the designs.
        if known is None:
            known = []
        identifier = self.get_design_identifier()
        if identifier not in known:
            known.append(identifier)
            design = self.get_design()
            if design is not None:
                return design.get_all_design_identifiers(known)
            else:
                # Broken design fallback to default.
                known.append('default')
        return known

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_role')
    def set_role(self, role):
        self._role = role

    security.declareProtected(
        SilvaPermissions.View, 'get_role')
    def get_role(self):
        return self._role

    security.declareProtected(
        SilvaPermissions.View, 'get_allowed_content_types')
    def get_allowed_content_types(self):
        return self._allowed_content_types

    security.declareProtected(
        SilvaPermissions.ChangeSilvaContent, 'set_allowed_content_types')
    def set_allowed_content_types(self, types):
        self._allowed_content_types = set(types)
        return self._allowed_content_types

    @property
    def slots(self):
        # XXX We can cache this on publication.
        return dict(
            map(lambda block: (block.identifier, block),
                filter(lambda block: IBlockSlot.providedBy(block),
                       map(operator.itemgetter(1),
                           IBlockManager(self).get_all()))))

    @property
    def markers(self):
        design = self.get_design()
        if design is not None:
            return design.markers
        return []

    def __call__(self, content, request, stack):
        design = self.get_design()
        if design is not None:
            return design(self, request, [self,] + stack)
        return None


InitializeClass(PageModelVersion)


class PageModel(VersionedObject, Folder):
    """ A Silva Page Model is content type that represents a template
    where you can add slots / default blocks and restrictions.
    """
    grok.implements(IPageModel)
    silvaconf.version_class(PageModelVersion)
    silvaconf.priority(-20)
    silvaconf.icon('model.png')

    meta_type = 'Silva Page Model'
    security = ClassSecurityInfo()


InitializeClass(PageModel)


class PageModelListing(ContainerListing):
    grok.name('pagemodels')
    grok.order(200)
    title = _(u'Page Model(s)')
    interface = IPageModel

    @classmethod
    def configuration(cls, screen):
        cfg = super(PageModelListing, cls).configuration(screen)
        cfg.update({'content_match': ['equal', 'access', 'manage']})
        return cfg


class PageModelAddForm(silvaforms.SMIAddForm):
    """ Add form for page models.
    """
    grok.name(PageModel.meta_type)
    fields = PageModelFields


class PageModelEdit(PageREST):
    grok.adapts(Screen, IPageModel)
    grok.name('content')
    grok.require('silva.ManageSilvaContentSettings')

    def payload(self):
        version = self.context.get_editable()
        if version is not None:
            view = getMultiAdapter(
                (version, self.request), IJSView, name='content-layout')
            return view(self, identifier=version.getId())

        view = getMultiAdapter(
            (self.context, self.request), IJSView, name='content-preview')
        return view(self)


class PageModelDesignForm(silvaforms.SMISubEditForm):
    grok.context(IPageModel)
    grok.view(Settings)
    grok.order(10)

    label = _(u"Page template")
    fields = PageModelFields.omit('id', 'title')


class EditMenu(ExpendableMenuItem):
    grok.adapts(ContentMenu, IPageModel)
    grok.order(10)

    name = _('Edit')
    screen = PageModelEdit


class PageModelView(silvaviews.View):
    grok.context(IPageModel)

    def render(self):
        design = self.content.get_design()
        if design is not None:
            render = design(self.content, self.request, [self.content])
            if render is not None:
                return render()
        msg = _('Sorry, this ${meta_type} is not viewable.',
                mapping={'meta_type': self.context.meta_type})
        return '<p>%s</p>' % translate(msg, context=self.request)


PAGE_TO_DESIGN_REF_NAME = u'page-to-design'


@grok.subscribe(IPage, IDesignAssociatedEvent)
def set_reference_to_page_model(page, event):
    if not IPageModelVersion.providedBy(event.design):
        return
    model = event.design.get_silva_object()
    reference_service = getUtility(IReferenceService)
    reference = reference_service.get_reference(
        page, name=PAGE_TO_DESIGN_REF_NAME, add=True)
    reference.set_target(model)

@grok.subscribe(IPage, IDesignDeassociatedEvent)
def remove_reference_to_page_model(page, event):
    if not IPageModelVersion.providedBy(event.design):
        return
    reference_service = getUtility(IReferenceService)
    reference_service.delete_reference(page, name=PAGE_TO_DESIGN_REF_NAME)

@grok.subscribe(IPageModel, IContentImported)
def register_if_published(model, event):
    version = model.get_viewable()
    if version is not None:
        service = getUtility(IContentLayoutService)
        service.register_page_model(version)

@grok.subscribe(IPageModelVersion, IContentPublishedEvent)
def register(version, event):
    service = getUtility(IContentLayoutService)
    service.register_page_model(version)


@grok.subscribe(IPageModelVersion, IObjectWillBeRemovedEvent)
@grok.subscribe(IPageModelVersion, IContentClosedEvent)
def unregister(version, event):
    # If we remove the root, we can't unregister
    if not IRoot.providedBy(event.object):
        service = getUtility(IContentLayoutService)
        service.unregister_page_model(version)
