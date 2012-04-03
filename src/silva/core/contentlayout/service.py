# -*- coding: utf-8 -*-
# (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt

from itertools import chain

from zope.component import IFactory
from zope.interface import Interface

from five import grok
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass

from silva.core import conf as silvaconf
from silva.core.interfaces import IAuthorizationManager
from silva.core.services.base import SilvaService
from silva.translations import translate as _
from zeam.form import silva as silvaforms

from Products.Silva.ExtensionRegistry import extensionRegistry
from Products.Silva import roleinfo

from silva.core.contentlayout import interfaces
from silva.core.contentlayout.designs.registry import registry


def get_content_class_from_content_type(content_type):
    #XXX: is this the correct way
    addable = extensionRegistry.get_addable(content_type)
    if addable is None:
        raise ValueError('Unknow content type %s' % content_type)
    return addable['instance']


class ContentLayoutService(SilvaService):
    """Design service provides security and other settings for content
    layout designs
    """
    grok.implements(interfaces.IContentLayoutService)
    grok.name('service_contentlayout')
    silvaconf.icon('service.png')
    meta_type = 'Silva ContentLayout Service'

    security = ClassSecurityInfo()
    manage_options = (
        {'label': 'Settings', 'action': 'manage_settings'},
        ) + SilvaService.manage_options

    _restrictions_index = {}
    _default_designs_index = {}


    @property
    def _restrictions(self):
        return set(chain.from_iterable(self._restrictions_index.itervalues()))

    @property
    def _default_designs(self):
        return set(self._default_designs_index.itervalues())

    security.declareProtected(
        'View Management Screens', 'lookup')
    def lookup(self, context):
        candidates = registry.lookup(context)
        return filter(
            lambda t: self._design_allowed_in_context(t, context),
            candidates)

    security.declareProtected(
        'View Management Screens', 'lookup_by_content_type')
    def lookup_by_content_type(self, content_type, parent):
        candidates = registry.lookup_by_content_type(content_type, parent)
        object_class = get_content_class_from_content_type(content_type)
        return filter(
            lambda t: self._design_allowed_in_context(
                t, parent, object_class=object_class),
            candidates)

    security.declareProtected(
        'View Management Screens', 'lookup_by_name')
    def lookup_by_name(self, name):
        return registry.lookup_by_name(name)

    security.declareProtected(
        'View Management Screens', 'default_design')
    def default_design(self, context):
        rule = self._default_designs_index.get(context.meta_type)
        if rule is not None and \
                self._design_allowed_in_context(rule.design, context):
            return rule.design
        return None

    security.declareProtected(
        'View Management Screens', 'default_design_by_content_type')
    def default_design_by_content_type(self, content_type, parent):
        rule = self._default_designs_index.get(content_type)
        content_class = get_content_class_from_content_type(content_type)
        if rule is not None and self._design_allowed_in_context(
                rule.design, parent, object_class=content_class):
            return rule.design
        return None

    security.declareProtected(
        'View Management Screens', 'update_restrictions')
    def update_restrictions(self, rules):
        for rule in rules:
            rule.validate()
        self._restrictions_index = {}
        for rule in rules:
            identifier = rule.design.get_identifier()
            if identifier not in self._restrictions_index:
                self._restrictions_index[identifier] = set()
            self._restrictions_index[identifier].add(rule)

    security.declareProtected(
        'View Management Screens', 'update_default_designs')
    def update_default_designs(self, rules):
        for rule in rules:
            rule.validate()
        self._default_designs_index = {}
        for rule in rules:
            self._default_designs_index[rule.content_type] = rule

    def _design_allowed_in_context(self, design, context,
                                     object_class=None):
        if object_class is None:
            object_class = context.__class__
        rules = self._restrictions_index.get(design.get_identifier())
        if rules is None:
            return True
        user_role = IAuthorizationManager(context).get_user_role()
        for rule in rules:
            if object_class.meta_type != rule.content_type:
                continue
            if roleinfo.isEqualToOrGreaterThan(user_role, rule.role):
                continue
            return False
        return True


InitializeClass(ContentLayoutService)


class ContentLayoutServiceManageSettings(silvaforms.ZMIComposedForm):
    """ Design Service configuration.
    """
    grok.name('manage_settings')
    grok.context(ContentLayoutService)

    label = _(u"Design Service configuration")
    description = _(u"Configure restrictions and defaults"
                    u" for content layout tempates")


class DesignContentRule(object):
    """ Base class for design / content rules.
    """
    grok.implements(interfaces.IDesignContentRule)

    def __init__(self, design, content_type):
        self.design = design
        self.content_type = content_type

    def __hash__(self):
        return hash((self.content_type, self.design.get_identifier()))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.design.get_identifier(), self.content_type) == \
            (other.design.get_identifier(), other.content_type)
        return (self.content_type, self.design.get_identifier())

    def validate(self):
        design_context_restriction = grok.context.bind().get(self.design)
        object_type = get_content_class_from_content_type(self.content_type)
        verify = lambda x: issubclass(object_type, x)
        if issubclass(design_context_restriction, Interface):
            verify = design_context_restriction.implementedBy
        if not verify(object_type):
            raise ValueError(_(u'Design %s restricts its usage to %s objects'
                               u', However %s do not comply') %
                             (self.design.label,
                              design_context_restriction.__name__,
                              self.content_type))


class DesignRestriction(DesignContentRule):
    """ Require a minimal role to set a design on a content.
    """

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
    grok.view(ContentLayoutServiceManageSettings)
    grok.order(10)

    label = _(u"Define designs access restrictions")
    fields = silvaforms.Fields(interfaces.IDesignRestrictions)
    ignoreContent = False
    ignoreRequest = True

    @silvaforms.action(_(u"Apply"))
    def save(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        try:
            self.context.update_restrictions(data['_restrictions'])
            self.status = _(u"Changes saved.")
        except ValueError as e:
            self.status = e.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS


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
    grok.view(ContentLayoutServiceManageSettings)
    grok.order(10)

    label = _(u"Define default design for content types")
    fields = silvaforms.Fields(interfaces.IContentDefaultDesigns)
    ignoreContent = False
    ignoreRequest = True

    @silvaforms.action(_(u"Apply"))
    def save(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        try:
            self.context.update_default_designs(data['_default_designs'])
            self.status = _(u"Changes saved.")
        except ValueError as e:
            self.status = e.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS
