from five import grok
from zope.interface import Interface

from silva.core.interfaces import (ISilvaObject, IDefaultContentTemplate,
                                   IGhost)
from silva.core.layout.interfaces import ISilvaLayer

grok.layer(ISilvaLayer)
class DefaultContentTemplate(grok.View):
    """The default content template for rendered Silva content which does not
       support IContentLayout.  This view wraps the rendered silva content 
       (passed in via set_content) with the desired default content template.
       The dct can add a left nav (or not), a title (at the appropriate heading
       level), etc.
       
       Override this in your own layer to provide a custom-tailored default
       content template for your own layout.  You can also create layouts
       tailored for specific content types by changing grok.context.
    """
    grok.context(ISilvaObject)
    grok.implements(IDefaultContentTemplate)
    grok.provides(IDefaultContentTemplate)
    grok.name(u'')
    
    #these need to be set before this view is called, they will be added to
    # the view template's namespace
    layout = None
    page = None
    rendered_content = None
    
    def default_namespace(self):
        ns = super(DefaultContentTemplate, self).default_namespace()
        ns['rendered_content'] = self.rendered_content
        ns['page'] = self.page
        ns['layout'] = self.layout
        return ns
    
class DefaultGhostTemplate(DefaultContentTemplate):
    """Default content template for Silva Ghosts.  Basically renders the
       haunted view in place of itself.
       
       What we want for ghosts are to _always_ only return the rendered_content
       itself.  No other templating or chroming should happen here.  This is
       the behavior of the default content template, however in order
       to ensure that extensions do not override this behavior for ghosts, we
       create our own view.
       
       As with anything ghosty, you need to be careful that the ghost gets
       out of the way as soon as possible, or you may end up with duplicate
       content on the screen (e.g. content within content) or something like
       that.
       
    """
    
    grok.context(IGhost)
    grok.name(u'')
    
