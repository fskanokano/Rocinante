# Rocinante

    Rocinante is a lightweight WSGI web application framework based on Werkzeug.

#### Installing

    pip install Rocinante

#### A Simple Example

    from rocinante import Rocinante, Request
    
    app = Rocinante(__name__)
    
    
    @app.route('/')
    def hello(request: Request):
        return 'hello world!'
    
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Request Arguments

Rocinante will only pass in the arguments that you need.

Make sure that these arguments declare types.

The original path arguments are not affected by these arguments. Rocinante knows how to handle it.

The supported arguments types are:

    Request, RequestHeaders, RequestCookies, RequestForm, RequestFiles, RequestArgs,RequestJSON, RequestBody

Example:

    from rocinante import Rocinante, RequestHandler, Request, RequestHeaders, RequestCookies, RequestForm, RequestFiles, \
        RequestArgs, RequestJSON, RequestBody
    
    app = Rocinante(__name__)
    
    
    class ArgumentsHandler(RequestHandler):
    
        # get all request arguments
        def get(
                self,
                request: Request,
                headers: RequestHeaders,
                cookies: RequestCookies,
                form: RequestForm,
                files: RequestFiles,
                args: RequestArgs,
                json: RequestJSON,
                body: RequestBody
        ):
            print(request)
            print(headers)
            print(cookies)
            print(form)
            print(files)
            print(args)
            print(json)
            print(body)
    
            return 'all request arguments'
    
        # get specific request arguments
        def post(
                self,
                cookies: RequestCookies,
                headers: RequestHeaders,
                body: RequestBody
        ):
            print(cookies)
            print(headers)
            print(body)
    
            return 'specific request arguments'
    
    
    class PathHandler(RequestHandler):
    
        def get(self, request: Request, path_id, headers: RequestHeaders):
            print(request)
            print(path_id)
            print(headers)
    
            return 'ok'
    
    
    app.add_handler('/arguments', ArgumentsHandler)
    app.add_handler('/path/<path_id>', PathHandler)
    
    if __name__ == '__main__':
        app.run()


#### Template

    from rocinante import Rocinante, Render, Request, RequestHeaders
    
    app = Rocinante(__name__)
    
    
    @app.route('/')
    def index(request: Request, headers: RequestHeaders):
        url = request.url
    
        return Render(
            # template path
            'templates/index.html',
            status=400,
            # pass the context to template
            url=url,
            headers=headers
        )
    
    
    if __name__ == '__main__':
        app.run()

#### Router

    from rocinante import Rocinante, RequestHandler, Router, Request, Url

    app = Rocinante(__name__)
    
    
    # other way to register handler
    class HelloHandler(RequestHandler):
    
        def get(self, request: Request):
            print(request.url)
            return 'get!'
    
        def post(self, request: Request):
            print(request.url)
            return 'post!'
    
    
    app.add_handler('/', HelloHandler)
    
    # use router
    router = Router()
    
    # different way to register handler
    
    # 1
    """"""
    
    
    @router.route('/test', methods=['GET', 'POST'])
    def router_handler(request: Request):
        if request.method == 'GET':
            return 'get!'
        elif request.method == 'POST':
            return 'post!'
    
    
    """"""
    
    # 2
    """"""
    
    
    class RouterHandler2(RequestHandler):
    
        def get(self):
            return 'get!'
    
        def post(self):
            return 'post!'
    
    
    router.add_handler('/test2', RouterHandler2)
    
    """"""
    
    # 3
    """"""
    
    
    class RouterHandler3(RequestHandler):
    
        def get(self):
            return 'get!'
    
        def post(self):
            return 'post!'
    
    
    urlpatterns = [
        Url('/test3', RouterHandler3)
    ]
    
    router.add_urlpatterns(urlpatterns)
    
    """"""
    
    # include router
    app.include_router(router, prefix='/router')
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Middleware

    from rocinante import Rocinante, Request, Response
    from rocinante.middleware import Middleware
    from rocinante.decorator import process_view_exempt
    
    app = Rocinante()
    
    
    class TestMiddleware(Middleware):
    
        def process_request(self, request: Request):
            print(request.url)
            request.url = 'process_request'
    
        def process_view(self, request: Request, view):
            print(request.url)
            request.url = 'process_view'
    
        def process_response(self, request: Request, response: Response):
            print(request.url)
            response.status = 400
    
    
    app.add_middleware(Middleware)
    
    
    @app.route('/')
    def index(request):
        print(request.url)
        return 'ok'
    
    
    @app.route('/exempt')
    # use this decorator to exempt from process view
    @process_view_exempt
    def exempt(request):
        print(request.url)
        return 'ok'
    
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Startup Event

    from rocinante import Rocinante
    
    app = Rocinante(__name__)
    
    
    @app.startup()
    def start():
        print('startup!')
    
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Mount WSGI Application And ASGI Application

    from rocinante import Rocinante
    from flask import Flask
    from fastapi import FastAPI
    
    app = Rocinante(__name__)
    
    flask_app = Flask(__name__)
    
    fastapi_app = FastAPI()
    
    
    @flask_app.route('/index')
    def flask_index():
        return 'flask index!'
    
    
    @fastapi_app.get('/index')
    def fastapi_index():
        return 'fastapi index!'
    
    
    app.mount_wsgi_app(flask_app, path='/flask')
    
    app.mount_asgi_app(fastapi_app, path='/fastapi')
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Integrate Extension

    from rocinante import Rocinante, RequestHandler
    from mysql.connector.pooling import MySQLConnectionPool
    
    app = Rocinante(__name__)
    
    # mysql config
    mysql_config = {
        'pool_size': 2,
        'host': '127.0.0.1',
        'port': 3306,
        'database': 'glow_serializer',
        'user': 'root',
        'password': '123456',
        'pool_reset_session': True
    }
    
    
    class MySQLMixin(object):
        mysql_pool = MySQLConnectionPool(**mysql_config)
    
    
    class MySQLHandler(RequestHandler, MySQLMixin):
    
        def get(self):
            connection = self.mysql_pool.get_connection()
            cursor = connection.cursor()
            sql = 'SELECT * FROM user'
            cursor.execute(sql)
            res = cursor.fetchall()
    
            cursor.close()
            connection.close()
    
            print(res)
    
            return res
    
    
    app.add_handler('/', MySQLHandler)
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000, debug=True)

#### Allow CORS

    from rocinante import Rocinante
    from rocinante.middleware import CORSMiddleware
    
    app = Rocinante(__name__)
    
    app.add_middleware(CORSMiddleware)
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Replace Request Class And Response Class

    from werkzeug import Response
    from rocinante import Rocinante, Request
    
    
    class MyRequest(Request):
    
        @property
        def my_property(self):
            return 'my request!'
    
    
    class MyResponse(Response):
    
        @property
        def my_property(self):
            return 'my response!'
    
    
    app = Rocinante(
        __name__,
        request_class=MyRequest,
        response_class=MyResponse
    )
    
    
    @app.route('/')
    def index(request: MyRequest):
        print(request.my_property)
        response = MyResponse('ok')
        print(response.my_property)
        return response
    
    
    if __name__ == '__main__':
        app.run()

#### Static File Handler

    from rocinante import Rocinante
    from rocinante.handler import StaticFileHandler
    
    app = Rocinante(__name__)
    
    app.add_static_file_handler(
        handler=StaticFileHandler,
        prefix='/images',
        file_dir='images'
    )
    
    app.add_static_file_handler(
        handler=StaticFileHandler,
        prefix='/videos',
        file_dir='videos'
    )
    
    if __name__ == '__main__':
        app.run()

#### Websocket

    from rocinante import Rocinante
    from rocinante.handler import WebsocketHandler
    
    app = Rocinante(__name__)
    
    
    class EchoWebsocketHandler(WebsocketHandler):
    
        def on_open(self):
            print("Connection opened")
    
        def on_message(self, message):
            print(f'Received message:{message}')
            self.send(message)
    
        def on_close(self, reason):
            print('Connection closed')
    
    
    app.add_websocket_handler('/echo', EchoWebsocketHandler)
    
    if __name__ == '__main__':
        app.run()

#### A Simple Chat Room Example

python

    from typing import List
    
    from rocinante import Rocinante
    from rocinante.handler import WebsocketHandler
    from geventwebsocket.websocket import WebSocket
    
    app = Rocinante(__name__)
    
    
    class ChatWebsocketHandler(WebsocketHandler):
        users: List[WebSocket] = []
    
        def on_open(self):
            self.users.append(self.ws)
    
            for ws in self.users:
                ws.send(f'User [{self.request.remote_addr}] entered the room.')
    
        def on_message(self, message):
            for user in self.users:
                user.send(f'User [{self.request.remote_addr}] said: {message}')
    
        def on_close(self, reason):
            self.users.remove(self.ws)
    
            for ws in self.users:
                ws.send(f'User [{self.request.remote_addr}] left the room.')
    
    
    app.add_websocket_handler('/chat', ChatWebsocketHandler)
    
    if __name__ == '__main__':
        app.run()

html

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>chat</title>
        <script src="http://apps.bdimg.com/libs/jquery/1.9.1/jquery.min.js"></script>
    </head>
    <body>
    <div id="chat" style="width: 500px;height: 500px;overflow: auto;border:solid 1px" readonly>
    </div>
    <div>
        <input type="text" id="content">
        <input type="button" id="send" value="send">
    </div>
    <script>
        let ws = new WebSocket('ws://127.0.0.1:8000/chat')
        ws.onmessage = function (e) {
            $('#chat').append('<p>' + e.data + '</p>')
        }
        $('#send').click(function () {
            let content = $('#content')
            ws.send(content.val())
            content.val('')
        })
    </script>
    </body>
    </html>

#### Integrate Socket.IO

    from rocinante import Rocinante
    import socketio
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    app = Rocinante(__name__)
    
    sio = socketio.Server(async_mode='gevent')
    
    
    class MyCustomNamespace(socketio.Namespace):
        def on_connect(self, sid, environ):
            pass
    
        def on_disconnect(self, sid):
            pass
    
        def on_my_event(self, sid, data):
            self.emit('my_response', data)
    
    
    sio.register_namespace(MyCustomNamespace('/test'))
    
    sio_app = socketio.WSGIApp(sio)
    
    app.mount_wsgi_app(sio_app, path='/socketio')
    
    if __name__ == '__main__':
        server = pywsgi.WSGIServer(('', 8000), sio_app, handler_class=WebSocketHandler)
        server.serve_forever()

#### Demos

    Check demos in the package "demos".
