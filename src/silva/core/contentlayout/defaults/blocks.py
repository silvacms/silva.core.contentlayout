# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import classImplements

from silva.core.contentlayout.interfaces import IBlockable
from silva.core.contentlayout.blocks import BlockView
from silva.translations import translate as _

# Silva Image

from Products.Silva.Image import Image

classImplements(Image, IBlockable)


class ImageBlock(BlockView):
    grok.context(Image)

    def render(self):
        return self.context.tag()


# Source block

from Products.SilvaExternalSources.SourceAsset import SourceAsset
from Products.SilvaExternalSources.errors import SourceError

classImplements(SourceAsset, IBlockable)


class SourceBlock(BlockView):
    grok.context(SourceAsset)

    def update(self):
        self.msg = None
        viewable = self.context.get_viewable()
        self.controller = None
        if viewable is not None:
            try:
                self.controller = viewable.get_controller(self.request)
            except SourceError, error:
                self.msg = error.to_html(request=self.request)
        else:
            self.msg = _(u"This component is not available.")

    def render(self):
        if self.msg:
            return self.msg
        return self.controller.render()


# Silva document

from silva.app.document.document import Document
from silva.core.editor.transform.interfaces import IDisplayFilter

classImplements(Document, IBlockable)


class DocumentBlock(BlockView):
    grok.context(Document)

    def render(self):
        viewable = self.context.get_viewable()
        if viewable is None:
            return _(u"This document is not available.")
        return viewable.body.render(viewable, self.request, IDisplayFilter)
