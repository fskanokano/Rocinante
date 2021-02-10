import json

from werkzeug.wrappers import Response


class JSONResponse(Response):
    def __init__(
            self,
            response=None,
            status=None,
            headers=None,
            mimetype='application/json',
            content_type=None,
            direct_passthrough=False,
    ):
        response = json.dumps(response)
        super().__init__(response, status, headers, mimetype, content_type, direct_passthrough)


class NotFoundResponse(Response):
    def __init__(
            self,
            response='Not Found',
            status=404,
            headers=None,
            mimetype=None,
            content_type=None,
            direct_passthrough=False,
    ):
        super().__init__(response, status, headers, mimetype, content_type, direct_passthrough)


class MethodNotAllowedResponse(Response):
    def __init__(
            self,
            response='Method Not Allowed',
            status=405,
            headers=None,
            mimetype=None,
            content_type=None,
            direct_passthrough=False,
    ):
        super().__init__(response, status, headers, mimetype, content_type, direct_passthrough)
