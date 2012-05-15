# package

from silva.core import conf as silvaconf

silvaconf.extension_name("silva.core.contentlayout")
silvaconf.extension_title("Silva Content Layout")
silvaconf.extension_system()

from silva.core.contentlayout.designs.design import Design
from silva.core.contentlayout.slots.slot import Slot
from silva.core.contentlayout.slots import restrictions
from silva.core.contentlayout.blocks import *

__all__ = ['Design', 'Slot', 'Block', 'BlockView', 'BlockController'
           'restrictions']
