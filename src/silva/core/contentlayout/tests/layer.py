from Products.Silva.testing import SilvaLayer

class ContentLayoutLayer(SilvaLayer):

    def _install_application(self, app):
        """make sure content layout is enabled"""
        
        super(ContentLayoutLayer, self)._install_application(app)
        app.root.service_extensions.install("silva.core.contentlayout")