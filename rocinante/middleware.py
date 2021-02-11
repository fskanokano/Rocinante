from werkzeug import Response

from .request import Request
from .application import Rocinante


class Middleware(object):

    def __init__(self, application: Rocinante):
        self.application = application

    def process_request(self, request: Request):
        pass

    def process_view(self, request: Request, view):
        pass

    def process_response(self, request: Request, response: Response):
        pass


class CORSMiddleware(Middleware):

    def process_response(self, request: Request, response: Response):
        origin = request.origin
        if origin is not None:
            response.headers.add_header('Access-Control-Allow-Origin', origin)
            response.headers.add_header('Access-Control-Allow-Credentials', 'true')
            response.headers.add_header('Access-Control-Expose-Headers',
                                        'Access-Control-Allow-Origin,Access-Control-Allow-Credentials')
        return response
