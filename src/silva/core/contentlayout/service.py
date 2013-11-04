# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt
# (c) 2012 Infrae. All rights reserved.

from itertools import chain

from zope.component import IFactory
from zope.component import getUtility
from zope.intid.interfaces import IIntIds
from zope.lifecycleevent import IObjectAddedEvent

from five import grok
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Acquisition import aq_parent

from silva.core import conf as silvaconf
from silva.core.interfaces import IAuthorizationManager, IRoot
from silva.core.interfaces import ISilvaConfigurableService
from silva.core.services.base import SilvaService
from silva.translations import translate as _
from silva.ui import menu
from zeam.form import silva as silvaforms

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva import roleinfo

from . import interfaces
from .blocks.registry import registry as block_registry
from .designs.registry import registry as design_registry
from .utils import verify_context


def get_content_class(content_type):
    #XXX: is this the correct way
    addable = extensionRegistry.get_addable(content_type)
    if addable is None:
        raise ValueError('Unknow content type %s' % content_type)
    return addable['instance']


class ContentLayoutService(SilvaService):
    """Design service provides security and other settings for content
    layout designs
    """
    grok.implements(interfaces.IContentLayoutService, ISilvaConfigurableService)
    grok.name('service_contentlayout')
    silvaconf.icon('service.png')
    meta_type = 'Silva ContentLayout Service'

    security = ClassSecurityInfo()
    manage_options = (
        {'label': 'Components', 'action': 'manage_components'},
        {'label': 'Templates', 'action': 'manage_templates'},
        ) + SilvaService.manage_options

    def __init__(self, id, title=None):
        super(ContentLayoutService, self).__init__(id, title)
        self._restrictions_index = {}
        self._default_designs_index = {}
        self._page_models = {}
        self._block_groups = [
            BlockGroup('Generic', ['text', 'site-content', 'source:cs_toc']),
            BlockGroup('Model', ['slot'])]

    security.declareProtected(
        'View Management Screens', 'get_restrictions')
    def get_restrictions(self):
        return set(chain.from_iterable(self._restrictions_index.itervalues()))

    security.declareProtected(
        'View Management Screens', 'get_default_designs')
    def get_default_designs(self):
        return set(self._default_designs_index.itervalues())

    security.declareProtected(
        'View Management Screens', 'set_restrictions')
    def set_restrictions(self, rules):
        for rule in rules:
            rule.validate(self)
        self._restrictions_index = {}
        for rule in rules:
            rules = self._restrictions_index.setdefault(rule.design, set())
            rules.add(rule)

    security.declareProtected(
        'View Management Screens', 'set_default_designs')
    def set_default_designs(self, rules):
        for rule in rules:
            rule.validate(self)
        self._default_designs_index = {}
        for rule in rules:
            self._default_designs_index[rule.content_type] = rule

    security.declareProtected(
        'View Management Screens', 'register_page_model')
    def register_page_model(self, model):
        int_id = getUtility(IIntIds).register(model)
        self._page_models[model.get_design_identifier()] = int_id
        self._p_changed = True

    security.declareProtected(
        'View Management Screens', 'unregister_page_model')
    def unregister_page_model(self, model):
        identifier = model.get_design_identifier()
        if identifier in self._page_models:
            del self._page_models[identifier]
            self._p_changed = True

    security.declareProtected(
        'View Management Screens', 'list_page_model')
    def list_page_model(self, context, meta_type):
        models = []
        resolve = getUtility(IIntIds).getObject
        user_role = 'Manager'
        if context is not None:
            user_role = IAuthorizationManager(context).get_user_role()
        for identifier in self._page_models.values():
            try:
                model = resolve(identifier)
            except KeyError:
                continue
            role = model.get_role()
            if (role is not None and
                not roleinfo.isEqualToOrGreaterThan(user_role, role)):
                continue
            if (meta_type is None and
                meta_type not in model.get_allowed_content_types()):
                continue
            models.append(model)

        return models

    def _design_allowed(self, design, context, meta_type):
        rules = self._restrictions_index.get(design.get_design_identifier())
        if rules is None:
            return True
        user_role = IAuthorizationManager(context).get_user_role()
        for rule in rules:
            if meta_type is not None and meta_type != rule.content_type:
                continue
            if roleinfo.isEqualToOrGreaterThan(user_role, rule.role):
                continue
            return False
        return True

    security.declareProtected(
        'View Management Screens', 'lookup_design')
    def lookup_design(self, context):
        meta_type = None
        results = design_registry.lookup_design(context)
        if context is not None:
            meta_type = context.meta_type
            results = filter(
                lambda design: self._design_allowed(design, context, meta_type),
                results)
        results += self.list_page_model(context, meta_type)
        return results

    security.declareProtected(
        'View Management Screens', 'lookup_design_by_addable')
    def lookup_design_by_addable(self, context, addable):
        meta_type = addable['name']
        results = filter(
            lambda design: self._design_allowed(design, context, meta_type),
            design_registry.lookup_design_by_addable(context, addable))
        results += self.list_page_model(context, meta_type)
        return results

    security.declareProtected(
        'View Management Screens', 'lookup_design_by_name')
    def lookup_design_by_name(self, name):
        model = self._page_models.get(name)
        if model:
            return getUtility(IIntIds).getObject(model)
        return design_registry.lookup_design_by_name(name)

    def _default_design(self, context, meta_type):
        rule = self._default_designs_index.get(meta_type)
        if rule is not None:
            design = self.lookup_design_by_name(rule.design)
            if design is not None:
                if self._design_allowed(design, context, meta_type):
                    return design
        return None

    security.declareProtected(
        'View Management Screens', 'default_design')
    def default_design(self, context):
        return self._default_design(context, context.meta_type)

    security.declareProtected(
        'View Management Screens', 'default_design_by_addable')
    def default_design_by_addable(self, context, addable):
        return self._default_design(context, addable['name'])

    # Blocks configuration

    security.declareProtected(
        'View Management Screens', 'get_block_groups')
    def get_block_groups(self):
        return list(self._block_groups)

    security.declareProtected(
        'View Management Screens', 'set_block_groups')
    def set_block_groups(self, groups):
        self._block_groups = groups

    security.declareProtected(
        'View Management Screens', 'lookup_block_by_name')
    def lookup_block_by_name(self, view, name):
        context = aq_parent(self)
        block = block_registry.lookup_block_by_name(context, name)
        if block is not None and block.is_available(view):
            return block
        return None

    security.declareProtected(
        'View Management Screens', 'lookup_block_groups')
    def lookup_block_groups(self, view):
        context = aq_parent(self)
        groups = []
        for group in self._block_groups:
            blocks = []
            if group.blocks is not None:
                for name in group.blocks:
                    block = block_registry.lookup_block_by_name(context, name)
                    if block is not None and block.is_available(view):
                        blocks.append(block)
            if blocks:
                groups.append({'title': group.title, 'blocks': blocks})
        return groups


InitializeClass(ContentLayoutService)


class ContentLayoutServiceManageTemplates(silvaforms.ZMIComposedForm):
    """ Design Service configuration.
    """
    grok.name('manage_templates')
    grok.context(ContentLayoutService)

    label = _(u"Template configuration")
    description = _(u"Configure restrictions and defaults"
                    u" for content layout tempates.")



class ContentLayoutServiceTemplatesConfiguration(silvaforms.ComposedConfigurationForm):
    grok.name('admin-templates')
    grok.context(ContentLayoutService)

    label = _(u"Template configuration")
    description = _(u"Configure restrictions and defaults"
                    u" for content layout tempates.")


class ContentLayoutServiceTemplatesConfigurationMenu(menu.MenuItem):
    grok.adapts(menu.ContentMenu, ContentLayoutService)
    grok.order(20)
    name = _('Templates')
    screen = ContentLayoutServiceTemplatesConfiguration


class DesignContentRule(object):
    """ Base class for design / content rules.
    """
    grok.implements(interfaces.IDesignContentRule)

    def __init__(self, design, content_type):
        self.design = design
        self.content_type = content_type

    def __hash__(self):
        # self.design is the design.get_identifier()
        return hash((self.content_type, self.design))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.design, self.content_type) == \
            (other.design, other.content_type)

    def validate(self, service):
        design = service.lookup_design_by_name(self.design)
        if design is None:
            raise ValueError(
                _(u"Template ${design} is not available.",
                  mapping=dict(design=self.design)))
        addable = get_content_class(self.content_type)
        comply, require = verify_context(design, addable, True)
        if not comply:
            raise ValueError(
                _(u'Template ${design} restricts its usage to ${require} '
                  u'objects, however ${content} do not comply.',
                  mapping=dict(design=design.get_design_title(),
                               require=require.__name__,
                               content=self.content_type)))


class DesignRestriction(DesignContentRule):
    """ Require a minimal role to set a design on a content.
    """
    grok.implements(interfaces.IDesignRestriction)

    def __init__(self, design, content_type, role):
        super(DesignRestriction, self).__init__(design, content_type)
        self.role = role


grok.global_utility(
    DesignRestriction,
    provides=IFactory,
    name=interfaces.IDesignRestriction.__identifier__,
    direct=True)


class DesignRestrictionsSettings(silvaforms.ZMISubForm):
    """Configure designs access restrictions.
    """
    grok.context(ContentLayoutService)
    grok.view(ContentLayoutServiceManageTemplates)
    grok.order(10)

    label = _(u"Define templates access restrictions")
    fields = silvaforms.Fields(interfaces.IDesignRestrictions)
    actions = silvaforms.Actions(silvaforms.EditAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False


class DesignRestrictionsConfiguration(silvaforms.SMISubForm):
    """Configure designs access restrictions.
    """
    grok.context(ContentLayoutService)
    grok.view(ContentLayoutServiceTemplatesConfiguration)
    grok.order(10)

    label = _(u"Define templates access restrictions")
    fields = silvaforms.Fields(interfaces.IDesignRestrictions)
    actions = silvaforms.Actions(
        silvaforms.CancelConfigurationAction(),
        silvaforms.EditAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False


class DefaultDesignRule(DesignContentRule):
    """Default design for a content type.
    """
    grok.implements(interfaces.IDefaultDesignRule)


grok.global_utility(
    DefaultDesignRule,
    provides=IFactory,
    name=interfaces.IDefaultDesignRule.__identifier__,
    direct=True)


class ContentDefaultDesignSettings(silvaforms.ZMISubForm):
    """Configure default design for content types
    """
    grok.context(ContentLayoutService)
    grok.view(ContentLayoutServiceManageTemplates)
    grok.order(10)

    label = _(u"Define default template for content types")
    fields = silvaforms.Fields(interfaces.IContentDefaultDesigns)
    actions = silvaforms.Actions(silvaforms.EditAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False



class ContentDefaultDesignConfiguration(silvaforms.SMISubForm):
    """Configure default design for content types
    """
    grok.context(ContentLayoutService)
    grok.view(ContentLayoutServiceTemplatesConfiguration)
    grok.order(10)

    label = _(u"Define default template for content types")
    fields = silvaforms.Fields(interfaces.IContentDefaultDesigns)
    actions = silvaforms.Actions(
        silvaforms.CancelConfigurationAction(),
        silvaforms.EditAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False


# Block configuration

class BlockGroup(object):
    """Group of blocks
    """
    grok.implements(interfaces.IBlockGroup)
    title = None
    blocks = None

    def __init__(self, title, blocks):
        self.title = title
        self.blocks = blocks


grok.global_utility(
    BlockGroup,
    provides=IFactory,
    name=interfaces.IBlockGroup.__identifier__,
    direct=True)


class ContentLayoutServiceManageBlocks(silvaforms.ZMIForm):
    """ Block Groups Service configuration.
    """
    grok.name('manage_components')
    grok.context(ContentLayoutService)

    label = _(u"Component palette configuration")
    description = _(u"Sort possible components into groups.")
    fields = silvaforms.Fields(interfaces.IBlockGroupsFields)
    actions = silvaforms.Actions(silvaforms.EditAction())
    dataManager = silvaforms.SilvaDataManager
    ignoreContent = False


class ContentLayoutServiceBlocksConfiguration(silvaforms.ConfigurationForm):
    grok.context(ContentLayoutService)

    label = _(u"Component palette configuration")
    description = _(u"Sort possible components into groups.")
    fields = silvaforms.Fields(interfaces.IBlockGroupsFields)
    actions = silvaforms.Actions(
        silvaforms.CancelConfigurationAction(),
        silvaforms.EditAction())


class ContentLayoutServiceBlocksConfigurationMenu(menu.MenuItem):
    grok.adapts(menu.ContentMenu, ContentLayoutService)
    grok.order(10)
    name = _('Component palette')
    screen = ContentLayoutServiceBlocksConfiguration


@grok.subscribe(interfaces.IContentLayoutService, IObjectAddedEvent)
def configure_models(service, event):
    root = aq_parent(service)
    if event.oldParent is None and IRoot.providedBy(root):
        extension = extensionRegistry.get_extension('silva.core.contentlayout')
        extension.installer.configure_content(root, extension)
