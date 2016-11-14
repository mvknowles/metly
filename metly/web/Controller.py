import os
from genshi.template import TemplateLoader


class Controller(object):

    def __init__(self, server_rpc):
        self.server_rpc = server_rpc
        self.loader = TemplateLoader(os.path.join(os.path.dirname(__file__), \
                'html'), auto_reload=True)

    def is_xhr(self):
        requested_with = cherrypy.request.headers.get('X-Requested-With')
        return requested_with and requested_with.lower() == 'xmlhttprequest'


    def render(self, template_path, **kwargs):
        if len(kwargs) == 0:
            kwargs = {"errors": {}}

        tmpl = self.loader.load(template_path)
        stream = tmpl.generate(**kwargs)
        return stream.render('html', doctype='html')
