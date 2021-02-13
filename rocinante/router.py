from typing import List, Type

from geventwebsocket import WebSocketApplication
from werkzeug.routing import Rule
from .url import Url


class Router(object):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self):
        self.rules = []
        self.websocket_rules = []

    def route(self, rule, *, methods=['GET']):
        self._check_methods(methods)

        def wrapper(fbv):
            fbv.allow_methods = methods
            self.rules.append(Rule(rule, endpoint=fbv))
            return fbv

        return wrapper

    def add_handler(self, rule, handler):
        self.rules.append(Rule(rule, endpoint=handler))

    def _check_methods(self, methods):
        for method in methods:
            if method.lower() not in self.http_method_names:
                raise Exception('Invalid methods')

    def add_urlpatterns(self, urlpatterns: List[Url]):
        for url in urlpatterns:
            self.add_handler(url.rule, url.handler)

    def add_websocket_handler(self, rule: str, handler: Type[WebSocketApplication]):
        if not issubclass(handler, WebSocketApplication):
            raise Exception('This handler must be subclass of "WebSocketApplication".')
        self.websocket_rules.append(Rule(rule, endpoint=handler))
