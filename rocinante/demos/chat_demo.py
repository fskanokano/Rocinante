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
