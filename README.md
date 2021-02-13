# Rocinante

    Rocinante is a lightweight WSGI web application framework based on Werkzeug.

#### Installing

    pip install Rocinante

#### A Simple Example

    from rocinante import Rocinante, Request
    
    app = Rocinante()
    
    
    @app.route('/')
    def hello(request: Request):
        return 'hello world!'
    
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Router

    from rocinante import Rocinante, RequestHandler, Router, Request, Url

    app = Rocinante()
    
    
    # other way to register handler
    class HelloHandler(RequestHandler):
    
        def get(self):
            print(self.url)
            return 'get!'
    
        def post(self):
            print(self.url)
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
    
    app = Rocinante()
    
    
    @app.startup()
    def start():
        print('startup!')
    
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Mount WSGI Application

    from rocinante import Rocinante
    from flask import Flask
    
    app = Rocinante()
    
    flask_app = Flask(__name__)
    
    
    @flask_app.route('/index')
    def flask_test():
        return 'flask_index!'
    
    
    app.mount_wsgi_app(flask_app, path='/flask')
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Integrated Extension

    from rocinante import Rocinante, RequestHandler
    from mysql.connector.pooling import MySQLConnectionPool
    
    app = Rocinante()
    
    
    # config class
    class MySQLConfig(object):
        pool_size = 2
        host = '127.0.0.1'
        port = 3306
        database = 'Rocinante'
        user = 'root'
        password = '123456'
        pool_reset_session = True
    
    
    # load config to app
    app.load_config('mysql', MySQLConfig)
    
    
    class MySQLMixin(object):
        def __init__(self, application: Rocinante):
            # get config from app
            mysql_config = application.get_config('mysql')
            self.mysql_pool = MySQLConnectionPool(**mysql_config)
    
    
    class MySQLHandler(RequestHandler, MySQLMixin):
    
        def get(self):
            connection = self.mysql_pool.get_connection()
            cursor = connection.cursor()
            sql = 'SELECT * FROM user'
            cursor.execute(sql)
            res = cursor.fetchall()
    
            connection.close()
            cursor.close()
    
            return res
    
    
    app.add_handler('/', MySQLHandler)
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000, debug=True)

#### Allow CORS

    from rocinante import Rocinante
    from rocinante.middleware import CORSMiddleware
    
    app = Rocinante()
    
    app.add_middleware(CORSMiddleware)
    
    if __name__ == '__main__':
        app.run('0.0.0.0', 8000)

#### Replace Request Class And Response Class

    from werkzeug import Request, Response
    from rocinante import Rocinante
    
    
    class MyRequest(Request):
    
        @property
        def my_property(self):
            return 'my request!'
    
    
    class MyResponse(Response):
    
        @property
        def my_property(self):
            return 'my response!'
    
    
    app = Rocinante(
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
    
    app = Rocinante()
    
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
    
    app = Rocinante()
    
    
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

    from typing import List
    
    from rocinante import Rocinante
    from rocinante.handler import WebsocketHandler
    from geventwebsocket.websocket import WebSocket
    
    app = Rocinante()
    
    
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

#### Integrate Socket.IO

    from rocinante import Rocinante
    import socketio
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    app = Rocinante()
    
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

    Check demos in the package "demos"
