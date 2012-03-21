# package

from silva.core import conf as silvaconf

silvaconf.extension_name("silva.core.contentlayout")
silvaconf.extension_title("Silva Content Layout")
silvaconf.extension_system()


from silva.core.contentlayout.templates.template import Template
from silva.core.contentlayout.slots.slot import Slot

__all__ = ['Template', 'Slot']
