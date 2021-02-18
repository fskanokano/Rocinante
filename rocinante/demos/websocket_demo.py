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
