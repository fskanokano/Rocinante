from .application import Rocinante
from .request import Request


class RequestHandler(object):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self, application: Rocinante, request: Request):
        self.application = application
        self.request = request
        self.url = request.url
        self.path = request.path
        self.json = request.json
        self.form = request.form
        self.args = request.args
        self.headers = request.headers
        self.cookies = request.cookies
        self.files = request.files

        # set mixin extension to handler
        for mixin_class in self._mixin_classes:
            mixin = mixin_class(application)
            mixin_extensions = [attr for attr in dir(mixin) if
                                not attr.startswith('__') and not callable(getattr(mixin, attr))]
            for mixin_extension in mixin_extensions:
                setattr(self, mixin_extension, getattr(mixin, mixin_extension))

    def reload_request(self, request: Request):
        self.__init__(
            application=self.application,
            request=request,
        )

    @property
    def _mixin_classes(self):
        return [cls for cls in self.__class__.__mro__ if 'Mixin' in cls.__name__]

    @property
    def implement_method(self):
        return [attr for attr in dir(self) if attr in self.http_method_names]
