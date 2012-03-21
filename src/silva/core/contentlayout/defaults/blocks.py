
from five import grok
from zope.interface import classImplements

import Products.Silva.Image
from silva.core.contentlayout.interfaces import IBlockable
from silva.core.contentlayout.blocks import BlockView


classImplements(Products.Silva.Image.Image, IBlockable)


class ImageBlock(BlockView):
    grok.context(Products.Silva.Image.Image)

    def render(self):
        return self.context.tag()
