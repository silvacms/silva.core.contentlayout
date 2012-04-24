
from five import grok
from grokcore.component.util import sort_components
from zope.testing import cleanup
from zope.interface import implementedBy
from zope.interface.interfaces import ISpecification

from AccessControl.security import checkPermission

from silva.core.contentlayout.interfaces import IDesignLookup


class Validator(object):
    """Validate if a design is usable in a given context (maybe for a
    given addable).
    """

    def __init__(self, context, addable=None):
        self.context = context
        self.addable = addable

    def __call__(self, design):
        if self.context is not None:
            required = grok.context.bind().get(design)
            if not ISpecification.providedBy(required):
                required = implementedBy(required)

            # If an addable is provided, we check the require on it.
            if self.addable is not None:
                if not required.implementedBy(self.addable):
                    return False
            elif not required.providedBy(self.context):
                return False

            permission = grok.require.bind().get(design)
            if permission:
                return checkPermission(permission, self.context)

        return True


class DesignRegistry(object):
    """Register designs
    """
    grok.implements(IDesignLookup)

    def __init__(self):
        self._designs = {}
        self._designs_by_name = {}

    def register_design(self, factory):
        context = grok.context.bind().get(factory)
        name = grok.name.bind().get(factory)
        if not name:
            raise ValueError('Design %r must defined a grok.name' % factory)
        if name in self._designs_by_name:
            raise ValueError(
                'Error while registering design %r, '
                'Design %r is already registered for name "%s"' %
                (factory, self._designs_by_name[name], name))
        self._designs_by_name[name] = factory
        factories = self._designs.setdefault(context, [])
        factories.append(factory)

    def remove(self, factory):
        self._designs

    def _lookup(self, validator):
        candidates = []
        for iface, factories in self._designs.iteritems():
            candidates.extend(filter(validator, factories))
        return sort_components(candidates)

    def lookup_design(self, context):
        return self._lookup(Validator(context))

    def lookup_design_by_name(self, name):
        return self._designs_by_name.get(name)

    def lookup_design_by_addable(self, context, addable):
        return self._lookup(Validator(context, addable['instance']))

    def default_design(self, context):
        return None

    def default_design_by_addable(self, context, addable):
        return None

    def clear(self):
        self._designs = {}


registry = DesignRegistry()
cleanup.addCleanUp(registry.clear)

grok.global_utility(
    registry,
    provides=IDesignLookup,
    direct=True)
