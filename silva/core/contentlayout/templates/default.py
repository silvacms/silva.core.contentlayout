from five import grok
from zope.interface import Interface

from silva.core.interfaces import ISilvaObject, IDefaultContentTemplate
from silva.core.layout.interfaces import ISilvaLayer

grok.layer(ISilvaLayer)
class DefaultContentTemplate(grok.View):
    """The default content template for rendered Silva content which does not
       support IContentLayout.  This view wraps the rendered silva content 
       (passed in via set_content) with the desires default content template.
       The dct can add a left nav (or not), a title (at the appropriate heading
       level), etc.
       
       Override this in your own layer to provide a custom-tailored default
       content template for your own layout.  You can also create layouts
       tailored for specific content types by changing the grok.context.
    """
    grok.context(ISilvaObject)
    grok.implements(IDefaultContentTemplate)
    grok.provides(IDefaultContentTemplate)
#    grok.name(u'contenttemplate.html')
    grok.name(u'')
    
    def set_content(self, rendered_content):
        self.rendered_content = rendered_content
        
    def default_namespace(self):
        ns = super(DefaultContentTemplate, self).default_namespace()
        ns['rendered_content'] = self.rendered_content
        return ns
    
