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
