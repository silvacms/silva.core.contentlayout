from five import grok

from silva.core.interfaces import ISilvaObject
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
    
    def set_content(self, rendered_content):
        self.rendered_content = rendered_content
        
    def render(self):
        return self.rendered_content
    
