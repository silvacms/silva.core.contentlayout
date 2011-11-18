
import uuid

from five import grok
from zope.publisher.interfaces.http import IHTTPRequest
from zope.interface import Interface
from zope.component import getUtility, queryMultiAdapter

from silva.core.interfaces import IDataManager
from silva.core.references.interfaces import IReferenceService
from silva.core.contentlayout.interfaces import IReferenceParameters
from silva.core.contentlayout.interfaces import IBlockView


class ReferenceParameters(object):
    grok.implements(IReferenceParameters)

    def __init__(self):
        self.identifier = unicode(uuid.uuid1())


class BoundReferenceBlock(grok.MultiAdapter):
    grok.adapts(IReferenceParameters, Interface, IHTTPRequest)
    grok.provides(IDataManager)

    def __init__(self, reference, context, request):
        self._name = reference.identifier
        self.context = context
        self.request = request
        self._service = getUtility(IReferenceService)

    def clear(self):
        self._service.delete_reference(self.context, name=self._name)

    def update(self, parameters):
        reference = self._service.get_reference(
            self.context, name=self._name, add=True)
        if isinstance(parameters, int):
            reference.set_target_id(parameters)
        else:
            reference.set_target(parameters)

    def render(self):
        reference = self._service.get_reference(self.context, name=self._name)
        if reference is None:
            return u'<p>reference is missing</p>'
        content = reference.target
        if content is None:
            return u'<p>reference is broken</p>'
        view = queryMultiAdapter((content, self.request), IBlockView)
        if view is None:
            return u'<p>block content is not viewable</p>'
        return view()


class BlockView(object):
    """A view on a block for an external content.
    """
    grok.implements(IBlockView)
    grok.baseclass()

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def default_namespace(self):
        namespace = {}
        namespace['view'] = self
        namespace['context'] = self.context
        namespace['request'] = self.request
        return namespace

    def namespace(self):
        return {}

    def update(self):
        pass

    def render(self):
        return self.template.render(self)

    render.base_method = True

    def __call__(self):
        self.update()
        return self.render()

