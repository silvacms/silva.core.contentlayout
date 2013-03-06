# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import uuid

from five import grok
from zope.event import notify
from zope.interface import Interface
from zope.lifecycleevent import ObjectModifiedEvent
from zope.publisher.interfaces.http import IHTTPRequest

from silva.core import conf as silvaconf
from silva.core.conf import schema as silvaschema
from silva.core.conf.interfaces import ITitledContent
from silva.core.editor.interfaces import ITextIndexEntries
from silva.core.editor.text import Text
from silva.core.editor.transform.interfaces import IInputEditorFilter
from silva.core.editor.transform.interfaces import ISaveEditorFilter
from silva.translations import translate as _
from silva.ui.rest.exceptions import RESTRedirectHandler
from zeam.form import silva as silvaforms

from . import Block, BlockController
from .contents import ReferenceBlock
from ..interfaces import ITextBlock, IPage


class TextBlock(Text, Block):
    grok.implements(ITextBlock)
    grok.name('text')
    grok.title(_(u"Text"))
    grok.order(0)
    silvaconf.icon('text.png')

    def __init__(self, identifier=None):
        if identifier is None:
            self.identifier = u'text block %s' % uuid.uuid1()
        else:
            self.identifier = unicode(identifier)
        super(TextBlock, self).__init__(self.identifier)


class TextBlockController(BlockController):
    grok.adapts(ITextBlock, Interface, IHTTPRequest)

    def editable(self):
        return True

    @apply
    def text():

        def getter(self):
            return self.block.render(
                self.context,
                self.request,
                type=IInputEditorFilter)

        def setter(self, value):
            self.block.save(
                self.context,
                self.request,
                value,
                type=ISaveEditorFilter)

        return property(getter, setter)

    def remove(self):
        self.block.truncate(
            self.context,
            self.request,
            type=ISaveEditorFilter)

    def indexes(self):
        return ITextIndexEntries(self.block).entries

    def fulltext(self):
        return self.block.fulltext(self.context, self.request)

    def render(self, view=None):
        return self.block.render(self.context, self.request)


class ITextBlockFields(Interface):
    text = silvaschema.HTMLText(
        title=_(u"Text"),
        required=True)


class AddTextBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Add')

    def get_extra_payload(self, form):
        adding = form.__parent__
        if adding.block_id is None:
            return {}
        return {
            'block_id': adding.block_id,
            'block_data': adding.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        adding = form.__parent__
        adding.add(TextBlock()).text = data['text']
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"New text added."))
        return silvaforms.SUCCESS


class AddTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(TextBlock, IPage)
    grok.name('add')

    label = _(u"Add some text")
    fields = silvaforms.Fields(ITextBlockFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        AddTextBlockAction())

    def __init__(self, context, request, configuration, restrictions):
        super(AddTextBlock, self).__init__(context, request)
        self.restrictions = restrictions
        self.configuration = configuration


class EditTextBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Save changes')

    def get_extra_payload(self, form):
        return {
            'block_id': form.__name__,
            'block_data': form.getContent().render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        manager = form.getContentData()
        manager.set('text', data.getWithDefault('text'))
        notify(ObjectModifiedEvent(form.context))
        form.send_message(_(u"Text modified."))
        return silvaforms.SUCCESS


class EditTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(ITextBlock, IPage)
    grok.name('edit')

    label = _(u"Edit text")
    fields = silvaforms.Fields(ITextBlockFields)
    actions = silvaforms.Actions(
        silvaforms.CancelAction())
    ignoreContent = False

    def __init__(self, block, context, request, controller, restrictions):
        super(EditTextBlock, self).__init__(context, request)
        self.block = block
        self.restrictions = restrictions
        self.setContentData(controller)

    @silvaforms.action(_('Convert'))
    def convert(self):
        raise RESTRedirectHandler('convert', relative=self, clear=True)

    actions += EditTextBlockAction()


class ConvertTextBlockAction(silvaforms.Action):
    grok.implements(
        silvaforms.IDefaultAction,
        silvaforms.IRESTExtraPayloadProvider,
        silvaforms.IRESTCloseOnSuccessAction)
    title = _('Convert')

    block = None
    block_id = None
    block_controller = None

    def get_extra_payload(self, form):
        return {
            'block_id': self.block_id,
            'block_data': self.block_controller.render(),
            'block_editable': True}

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return silvaforms.FAILURE
        api = form.__parent__.__parent__
        container = form.context.get_container()
        factory = container.manage_addProduct['silva.app.document']
        factory.manage_addDocument(data['id'], data['title'])
        document = container._getOb(data['id'])
        version = document.get_editable()
        version.body.save(
            version,
            form.request,
            api.block_controller.text,
            type=ISaveEditorFilter)
        self.block_id = api.manager.replace(api.block_id, ReferenceBlock())
        self.block, self.block_controller = api.manager.get(self.block_id)
        self.block_controller.content = document
        notify(ObjectModifiedEvent(version))
        notify(ObjectModifiedEvent(form.context))
        return silvaforms.SUCCESS


class ConvertTextBlock(silvaforms.RESTPopupForm):
    grok.adapts(EditTextBlock, IPage)
    grok.name('convert')

    label = _(u"Convert text to a document")
    description = _(u"Convert text to a standalone document, and refer to it "
                    u"using a site content component.")
    fields = silvaforms.Fields(ITitledContent)
    actions = silvaforms.Actions(
        silvaforms.CancelAction(),
        ConvertTextBlockAction())

