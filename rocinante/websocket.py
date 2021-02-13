from geventwebsocket.resource import Resource


class WebsocketResource(Resource):

    def __get__(self, instance, owner):
        return self.__class__(
            apps=instance.websocket_apps
        )
