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
        super().__init__(
            response,
            status,
            headers,
            mimetype,
            content_type,
            direct_passthrough
        )


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
        super().__init__(
            response,
            status,
            headers,
            mimetype,
            content_type,
            direct_passthrough
        )


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
        super().__init__(
            response,
            status,
            headers,
            mimetype,
            content_type,
            direct_passthrough
        )


class Render(object):

    def __init__(self,
                 template_path,
                 status=None,
                 headers=None,
                 mimetype='text/html',
                 content_type=None,
                 direct_passthrough=None,
                 application=None,
                 **context
                 ):
        self.template_path = template_path
        self.status = status
        self.headers = headers
        self.mimetype = mimetype
        self.content_type = content_type
        self.direct_passthrough = direct_passthrough
        self.context = context

        if application is not None:
            template_environment = application.template_environment

            template = template_environment.get_template(template_path)

            self.html_content = template.render(**context)

    def reload_render(self, application):
        self.__init__(
            self.template_path,
            self.status,
            self.headers,
            self.mimetype,
            self.content_type,
            self.direct_passthrough,
            application,
            **self.context
        )

    def render(self):
        return Response(
            self.html_content,
            self.status,
            self.headers,
            self.mimetype,
            self.content_type,
            self.direct_passthrough
        )
