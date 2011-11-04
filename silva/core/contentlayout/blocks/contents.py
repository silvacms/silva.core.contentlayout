

from zope.interface import classImplements
from silva.core.contentlayout.interfaces import IPageBlock
import Products.Silva.Image

classImplements(Products.Silva.Image.Image, IPageBlock)


