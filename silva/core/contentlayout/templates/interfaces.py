
from zope.interface import Interface, Attribute

class InvalidModel(ValueError):
   pass


class InvalidSlot(KeyError):
   pass


class ITemplate(Interface):
   label = Attribute("user-friendly name of template")
   description = Attribute("a description of the template")
   slots = Attribute("a dictionary of slot definition in the template")

   def update():
      """Method called before the template is rendered.
      """


class ISlot(Interface):
   fill_in = Attribute("fill-in stragegy")

