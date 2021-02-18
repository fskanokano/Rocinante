import os
import traceback

from geventwebsocket import WebSocketError
from geventwebsocket.resource import WebSocketApplication
from geventwebsocket.websocket import WebSocket

from .application import Rocinante
from .request import Request
from .response import Response, JSONResponse, NotFoundResponse
from .mime_type_mapping import MIME_TYPE_MAPPING


class RequestHandler(object):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self, application: Rocinante):
        self.application = application

    def _set_extension(self):
        """
        This method is deprecated since Rocinante 1.6.
        """
        for mixin_class in self._mixin_classes:
            mixin = mixin_class(self.application)
            mixin_extensions = [attr for attr in dir(mixin) if
                                not attr.startswith('__') and not callable(getattr(mixin, attr))]
            for mixin_extension in mixin_extensions:
                setattr(self, mixin_extension, getattr(mixin, mixin_extension))

    @property
    def _mixin_classes(self):
        return [cls for cls in self.__class__.__mro__ if 'Mixin' in cls.__name__]

    @property
    def implement_method(self):
        return [attr for attr in dir(self) if attr in self.http_method_names]


class StaticFileHandler(RequestHandler):

    def get(self, request: Request, filename: str):

        filename_split = filename.split('.')

        if 2 <= len(filename_split) <= 3:
            if len(filename_split) == 2:
                image_type = filename_split[1]
            else:
                image_type = filename_split[1] + '.' + filename_split[2]

            if image_type not in MIME_TYPE_MAPPING.keys():
                return JSONResponse(
                    {
                        'error': 'Unsupported file type.'
                    }
                )

            handler_name = request.path.split('/')[1]
            file_dir = self.application.static_file_handlers['/' + handler_name]
            file_path = os.path.join(file_dir, filename)

            try:
                with open(file_path, 'rb') as f:
                    file = f.read()

                return Response(
                    file,
                    mimetype=MIME_TYPE_MAPPING[image_type]
                )

            except FileNotFoundError:
                return NotFoundResponse()

            except:
                traceback.print_exc()
                return JSONResponse(
                    {
                        'error': 'Failed to read file.'
                    },
                    status=400
                )

        else:
            return JSONResponse(
                {
                    'error': 'Invalid file name.'
                }
            )


class WebsocketHandler(WebSocketApplication):

    def __init__(self, ws):
        super().__init__(ws)
        self.ws: WebSocket = ws
        self.request = Request(self.ws.environ)

    def on_open(self):
        pass

    def on_message(self, message):
        self.send(message)

    def on_close(self, reason):
        pass

    def close(self, code: int = 1000, message: str = ''):
        message = message.encode()
        self.ws.close(code, message)

    def send(self, message):
        self.ws.send(message)

    def handle(self):
        self.protocol.on_open()

        while True:
            try:
                message = self.ws.receive()
            except WebSocketError:
                self.protocol.on_close()
                break

            if not self.ws.closed:
                self.protocol.on_message(message)
