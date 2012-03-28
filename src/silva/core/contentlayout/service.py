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
from silva.core.contentlayout.templates.registry import registry


def get_content_class_from_content_type(content_type):
    #XXX: is this the correct way
    addable = extensionRegistry.get_addable(content_type)
    if addable is None:
        raise ValueError('Unknow content type %s' % content_type)
    return addable['instance']


class ContentLayoutService(SilvaService):
    """Template service provides security and other settings for content
    layout templates
    """
    grok.implements(interfaces.IContentLayoutService)
    grok.name('service_contentlayout')
    silvaconf.icon('service.png')
    meta_type = 'Silva Template Service'

    security = ClassSecurityInfo()
    manage_options = (
        {'label': 'Settings', 'action': 'manage_settings'},
        ) + SilvaService.manage_options

    _restrictions_index = {}
    _default_templates_index = {}


    @property
    def _restrictions(self):
        return set(chain.from_iterable(self._restrictions_index.itervalues()))

    @property
    def _default_templates(self):
        return set(self._default_templates_index.itervalues())

    security.declareProtected(
        'View Management Screens', 'lookup')
    def lookup(self, context):
        candidates = registry.lookup(context)
        return filter(
            lambda t: self._template_allowed_in_context(t, context),
            candidates)

    security.declareProtected(
        'View Management Screens', 'lookup_by_content_type')
    def lookup_by_content_type(self, content_type, parent):
        candidates = registry.lookup_by_content_type(content_type, parent)
        object_class = get_content_class_from_content_type(content_type)
        return filter(
            lambda t: self._template_allowed_in_context(
                t, parent, object_class=object_class),
            candidates)

    security.declareProtected(
        'View Management Screens', 'default_template')
    def default_template(self, context):
        rule = self._default_templates_index.get(context.meta_type)
        if rule is not None and \
                self._template_allowed_in_context(rule.template, context):
            return rule.template
        return None

    security.declareProtected(
        'View Management Screens', 'default_template_by_content_type')
    def default_template_by_content_type(self, content_type, parent):
        rule = self._default_templates_index.get(content_type)
        content_class = get_content_class_from_content_type(content_type)
        if rule is not None and self._template_allowed_in_context(
                rule.template, parent, object_class=content_class):
            return rule.template
        return None

    security.declareProtected(
        'View Management Screens', 'update_restrictions')
    def update_restrictions(self, rules):
        for rule in rules:
            rule.validate()
        self._restrictions_index = {}
        for rule in rules:
            identifier = rule.template.get_identifier()
            if identifier not in self._restrictions_index:
                self._restrictions_index[identifier] = set()
            self._restrictions_index[identifier].add(rule)

    security.declareProtected(
        'View Management Screens', 'update_default_templates')
    def update_default_templates(self, rules):
        for rule in rules:
            rule.validate()
        self._default_templates_index = {}
        for rule in rules:
            self._default_templates_index[rule.content_type] = rule

    def _template_allowed_in_context(self, template, context,
                                     object_class=None):
        if object_class is None:
            object_class = context.__class__
        rules = self._restrictions_index.get(template.get_identifier())
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
    """ Template Service configuration.
    """
    grok.name('manage_settings')
    grok.context(ContentLayoutService)

    label = _(u"Template Service configuration")
    description = _(u"Configure restrictions and defaults"
                    u" for content layout tempates")


class TemplateContentRule(object):
    """ Base class for template / content rules.
    """
    grok.implements(interfaces.ITemplateContentRule)

    def __init__(self, template, content_type):
        self.template = template
        self.content_type = content_type

    def __hash__(self):
        return hash((self.content_type, self.template.get_identifier()))

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return (self.template.get_identifier(), self.content_type) == \
            (other.template.get_identifier(), other.content_type)
        return (self.content_type, self.template.get_identifier())

    def validate(self):
        template_context_restriction = grok.context.bind().get(self.template)
        object_type = get_content_class_from_content_type(self.content_type)
        verify = lambda x: issubclass(object_type, x)
        if issubclass(template_context_restriction, Interface):
            verify = template_context_restriction.implementedBy
        if not verify(object_type):
            raise ValueError(_(u'Template %s restricts its usage to %s objects'
                               u', However %s do not comply') %
                             (self.template.label,
                              template_context_restriction.__name__,
                              self.content_type))


class TemplateRestriction(TemplateContentRule):
    """ Require a minimal role to set a template on a content.
    """

    def __init__(self, template, content_type, role):
        super(TemplateRestriction, self).__init__(template, content_type)
        self.role = role


grok.global_utility(
    TemplateRestriction,
    provides=IFactory,
    name=interfaces.ITemplateRestriction.__identifier__,
    direct=True)


class TemplateRestrictionsSettings(silvaforms.ZMISubForm):
    """Configure templates access restrictions.
    """
    grok.context(ContentLayoutService)
    grok.view(ContentLayoutServiceManageSettings)
    grok.order(10)

    label = _(u"Define templates access restrictions")
    fields = silvaforms.Fields(interfaces.ITemplateRestrictions)
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


class DefaultTemplateRule(TemplateContentRule):
    """Default template for a content type.
    """
    grok.implements(interfaces.IDefaultTemplateRule)


grok.global_utility(
    DefaultTemplateRule,
    provides=IFactory,
    name=interfaces.IDefaultTemplateRule.__identifier__,
    direct=True)


class ContentDefaultTemplateSettings(silvaforms.ZMISubForm):
    """Configure default template for content types
    """
    grok.context(ContentLayoutService)
    grok.view(ContentLayoutServiceManageSettings)
    grok.order(10)

    label = _(u"Define default template for content types")
    fields = silvaforms.Fields(interfaces.IContentDefaultTemplates)
    ignoreContent = False
    ignoreRequest = True

    @silvaforms.action(_(u"Apply"))
    def save(self):
        data, errors = self.extractData()
        if errors:
            return silvaforms.FAILURE
        try:
            self.context.update_default_templates(data['_default_templates'])
            self.status = _(u"Changes saved.")
        except ValueError as e:
            self.status = e.args[0]
            return silvaforms.FAILURE
        return silvaforms.SUCCESS