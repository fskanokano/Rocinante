import json
import os
from typing import Type
from inspect import isfunction
from typing import Callable
from collections import Iterable, OrderedDict

from werkzeug import run_simple, Response
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map, Rule
from werkzeug.wsgi import ClosingIterator
from geventwebsocket.resource import WebSocketApplication
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler as GeventWebSocketHandler
from a2wsgi import ASGIMiddleware
from jinja2 import Environment, FileSystemLoader

from .request import Request
from .response import Render
from .config import Config
from .cache import HandlerLRUCache
from .websocket import WebsocketResource
from .request_arguments_types import SUPPORT_ARGUMENTS_MAPPING


class Rocinante(object):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    url_map = Map()

    _middlewares = []

    _config = Config

    _mounted_wsgi_apps = {}

    _cache = HandlerLRUCache()

    static_file_handlers = {}

    _websocket_resource = WebsocketResource()

    websocket_apps = OrderedDict()

    websocket_url_map = Map()

    def __init__(
            self,
            import_name: str,
            request_class: Type[Request] = Request,
            response_class: Type[Response] = Response,
            json_response_class: Type[Response] = None,
            not_found_response_class: Type[Response] = None,
            method_not_allowed_response_class: [Response] = None,
            handler_cache_capacity: int = 128
    ):
        """
        accept subclass of Rocinante.Request or subclass of werkzeug.Response
        """

        file_loader = self._get_file_loader(import_name)
        self.template_environment = Environment(loader=file_loader)

        # make sure request class and response class is correct
        self._check_request_class(request_class)

        self._check_response_class(
            response_class
        )

        self._check_processed_response_class(
            json_response_class,
            not_found_response_class,
            method_not_allowed_response_class
        )

        self.request_class = request_class
        self.response_class = response_class
        self.handler_cache_capacity = handler_cache_capacity

        if json_response_class is None:
            self.json_response_class = self._generate_json_response_class()
        else:
            self.json_response_class = json_response_class

        if not_found_response_class is None:
            self.not_found_response_class = self._generate_not_found_response_class()
        else:
            self.not_found_response_class = not_found_response_class

        if method_not_allowed_response_class is None:
            self.method_not_allowed_response_class = self._generate_method_not_allowed_response_class()
        else:
            self.method_not_allowed_response_class = method_not_allowed_response_class

    def wsgi_app(self, environ: dict, start_response):

        request = self.request_class(environ)

        # iterate process_request of middlewares
        _process_request = self._iter_process_request(request)
        if isinstance(_process_request, Response):
            return _process_request(environ, start_response)

        # try to get cached handler
        cached_dict = self._cache.get(request.path)

        # success get cached endpoint
        # only handle cbv
        if cached_dict is not None:
            handler = cached_dict['handler']
            kwargs = cached_dict['kwargs']

            response = self._handle_cbv(request, handler, kwargs, environ, start_response)
            # If the response is complete
            if isinstance(response, ClosingIterator):
                return response

        # cannot get cached handler
        else:

            # get adapter
            adapter = self.url_map.bind_to_environ(environ)

            # try to match the endpoint and kwargs
            try:
                endpoint, kwargs = adapter.match()

                # If the response is complete
                check_static_file_url = self._check_static_file_url(request, kwargs, environ, start_response)
                if isinstance(check_static_file_url, ClosingIterator):
                    return check_static_file_url

            except NotFound:

                # try to match mounted wsgi apps
                for path, wsgi_app in self._mounted_wsgi_apps.items():
                    if request.path.startswith(path):
                        environ = self._process_environ(environ, request, path)
                        mounted_wsgi_app_response = wsgi_app(environ, start_response)
                        return mounted_wsgi_app_response

                return self.not_found_response_class()(environ, start_response)

            # handle fbv
            if isfunction(endpoint):

                response = self._handle_fbv(request, endpoint, kwargs, environ, start_response)
                # If the response is complete
                if isinstance(response, ClosingIterator):
                    return response
            else:
                handler = endpoint(application=self)

                self._cache.set(request.path, {
                    'handler': handler,
                    'kwargs': kwargs
                })

                response = self._handle_cbv(request, handler, kwargs, environ, start_response)
                # If the response is complete
                if isinstance(response, ClosingIterator):
                    return response

        # process object not the instance of Response class
        if not isinstance(response, Response):
            response = self._process_response(response)

        # iterate process_response of middlewares
        response = self._iter_process_response(request, response)

        # call response object and return it
        return response(environ, start_response)

    def websocket_app(self, environ: dict, start_response):
        # get adapter
        adapter = self.websocket_url_map.bind_to_environ(environ)

        try:
            adapter.match()

            return self._websocket_resource(environ, start_response)

        except NotFound:
            return self.not_found_response_class()(environ, start_response)

    def add_websocket_handler(self, rule: str, handler: Type[WebSocketApplication]):
        if not issubclass(handler, WebSocketApplication):
            raise Exception('This handler must be subclass of "WebSocketApplication".')
        self.websocket_url_map.add(Rule(rule, endpoint=handler))
        self.websocket_apps[rule] = handler

    def route(self, rule, *, methods=['GET']):
        self._check_methods(methods)

        def wrapper(fbv):
            fbv.allow_methods = methods
            self.url_map.add(Rule(rule, endpoint=fbv))
            return fbv

        return wrapper

    def add_handler(self, rule, handler):
        self.url_map.add(Rule(rule, endpoint=handler))

    def add_static_file_handler(self, handler, *, prefix: str, file_dir: str):
        if not prefix.startswith('/'):
            raise Exception('Invalid prefix.')

        if prefix in self.static_file_handlers.keys():
            raise Exception('This handler prefix is already exists.')

        rule = prefix + '/<filename>'
        self.url_map.add(Rule(rule, endpoint=handler))
        self.static_file_handlers[prefix] = file_dir

    @staticmethod
    def startup():
        def wrapper(event):
            event()
            return event

        return wrapper

    def include_router(self, router, *, prefix: str = None):
        if not prefix.startswith('/'):
            raise Exception('Invalid prefix.')

        for rule in router.rules:
            if prefix is None:
                self.url_map.add(rule)
            else:
                self.url_map.add(Rule(prefix + rule.rule, endpoint=rule.endpoint))

        for websocket_rule in router.websocket_rules:
            if prefix is None:
                self.websocket_url_map.add(websocket_rule)
                self.websocket_apps[websocket_rule.rule] = websocket_rule.endpoint
            else:
                self.websocket_url_map.add(Rule(prefix + websocket_rule.rule, endpoint=websocket_rule.endpoint))
                self.websocket_apps[prefix + websocket_rule.rule] = websocket_rule.endpoint

    def add_middleware(self, middleware, **kwargs):
        self._middlewares.append(middleware(self, **kwargs))

    def load_config(self, name, config):
        self._config.set_config(name, config)

    def get_config(self, name):
        return self._config.get_config(name)

    def mount_wsgi_app(self, app: Callable, *, path: str):

        if not path.startswith('/'):
            raise Exception('Invalid path.')

        if not callable(app):
            raise Exception('Invalid wsgi application.')

        self._mounted_wsgi_apps[path] = app

    def mount_asgi_app(self, app: Callable, *, path: str):

        if not callable(app):
            raise Exception('Invalid asgi application.')

        wsgi_app = ASGIMiddleware(app)

        self.mount_wsgi_app(wsgi_app, path=path)

    def run(self, host: str = '0.0.0.0', port: int = 8000, *, debug: bool = True):

        if not self.websocket_apps:
            run_simple(host, port, self, use_debugger=debug, use_reloader=debug)

        else:
            print('Detected websocket, use gevent to run.')
            server = WSGIServer((host, port), self, handler_class=GeventWebSocketHandler)
            server.serve_forever()

    @staticmethod
    def _get_file_loader(import_name: str):
        root_dir = os.path.dirname(os.path.abspath(import_name))
        loader = FileSystemLoader(root_dir)
        return loader

    def _build_request_arguments(self, original_arguments: dict, request: Request, annotations: dict):
        request_arguments = {}

        reverse_annotations = {
            value: key for key, value in annotations.items() if key not in original_arguments
        }

        adapted_arguments_mapping = self._adapt_arguments_mapping(reverse_annotations)

        args_mapping = {
            key: {'position_name': value, 'mapping_name': adapted_arguments_mapping[key]} for key, value in
            reverse_annotations.items()
        }

        for arg_type, arg_name_dict in args_mapping.items():
            position_name = arg_name_dict['position_name']
            mapping_name = arg_name_dict['mapping_name']
            if mapping_name == 'request':
                request_arguments[position_name] = request
            else:
                request_arguments[position_name] = getattr(request, mapping_name)

        request_arguments.update(original_arguments)

        return request_arguments

    @staticmethod
    def _adapt_arguments_mapping(reverse_annotations: dict):

        adapted_arguments_mapping = SUPPORT_ARGUMENTS_MAPPING.copy()

        for arg_type in reverse_annotations:

            if SUPPORT_ARGUMENTS_MAPPING.get(arg_type, None) is None:

                adapted = False

                for support_type in SUPPORT_ARGUMENTS_MAPPING:
                    if issubclass(arg_type, support_type):
                        adapted_arguments_mapping[arg_type] = adapted_arguments_mapping.pop(support_type)
                        adapted = True
                        break

                if not adapted:
                    raise Exception(
                        f'Unsupported request argument:{reverse_annotations[arg_type]}. Wrong argument type:{arg_type}'
                    )

        return adapted_arguments_mapping

    def _check_static_file_url(self, request, kwargs, environ, start_response):
        for static_file_handlers_prefix in self.static_file_handlers.keys():
            if request.path.startswith(static_file_handlers_prefix):
                filename = kwargs['filename']
                file_dir = self.static_file_handlers[static_file_handlers_prefix]
                file_path = os.path.join(file_dir, filename)
                if not os.path.exists(file_path):
                    return self.not_found_response_class()(environ, start_response)

    def _handle_cbv(self, request, handler, kwargs, environ, start_response):
        method = getattr(handler, request.method.lower(), None)
        if method is None:
            implement_method = handler.implement_method
            if len(implement_method) >= 1:
                return self.method_not_allowed_response_class()(environ, start_response)
            else:
                return self.not_found_response_class()(environ, start_response)

        # iterate process_view of middlewares
        _process_view = self._iter_process_view(request, method)
        if isinstance(_process_view, Response):
            return _process_view(environ, start_response)

        request_arguments = self._build_request_arguments(kwargs, request, method.__annotations__)

        response = method(**request_arguments)
        return response

    def _handle_fbv(self, request, endpoint, kwargs, environ, start_response):
        allow_methods = endpoint.allow_methods
        if request.method not in allow_methods:
            return self.method_not_allowed_response_class()(environ, start_response)

        # iterate process_view of middlewares
        _process_view = self._iter_process_view(request, endpoint)
        if isinstance(_process_view, Response):
            return _process_view(environ, start_response)

        request_arguments = self._build_request_arguments(kwargs, request, endpoint.__annotations__)

        response = endpoint(**request_arguments)
        return response

    def _process_response(self, response):
        if isinstance(response, tuple):
            if len(response) < 1 or len(response) > 2:
                raise Exception('Invalid tuple.')
            if len(response) == 1:
                content = response[0]
                status_code = 200
            elif len(response) == 2:
                content = response[0]
                status_code = response[1]
            if not isinstance(content, Iterable):
                raise Exception('Invalid Iterable object.')
            if not isinstance(status_code, int):
                raise Exception('Invalid status code.')
            processed_response = self._make_response(content, status_code)

        # process the render response
        elif isinstance(response, Render):
            response.reload_render(self)
            processed_response = response.render()

        else:
            if not isinstance(response, Iterable):
                raise Exception('Invalid Iterable object.')
            processed_response = self._make_response(response)
        return processed_response

    @staticmethod
    def _check_request_class(*request_classes):
        for request_class in request_classes:
            if not issubclass(request_class, Request):
                raise Exception('Invalid request class.')

    @staticmethod
    def _check_response_class(*response_classes):
        for response_class in response_classes:
            if not issubclass(response_class, Response):
                raise Exception('Invalid response class.')

    @staticmethod
    def _check_processed_response_class(*processed_response_classes):
        for processed_response_class in processed_response_classes:
            if processed_response_class is not None:
                if not issubclass(processed_response_class, Response):
                    raise Exception('Invalid response class.')

    def _generate_json_response_class(self):

        class JSONResponse(self.response_class):

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

        return JSONResponse

    def _generate_not_found_response_class(self):

        class NotFoundResponse(self.response_class):

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

        return NotFoundResponse

    def _generate_method_not_allowed_response_class(self):

        class MethodNotAllowedResponse(self.response_class):

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

        return MethodNotAllowedResponse

    @staticmethod
    def _process_environ(environ, request, path):
        wsgi_app_url_location = len(path)
        wsgi_app_url = request.path[wsgi_app_url_location:]
        environ['PATH_INFO'] = wsgi_app_url
        environ['REQUEST_URI'] = wsgi_app_url
        environ['RAW_URI'] = wsgi_app_url
        return environ

    def _make_response(self, content, status=None):
        if isinstance(content, Iterable):
            return self.json_response_class(content, status)

    def _iter_process_request(self, request):
        for middleware in self._middlewares:
            _process_request = middleware.process_request(request)
            if isinstance(_process_request, Response):
                return _process_request

    def _iter_process_view(self, request, view):
        for middleware in self._middlewares:
            process_view_exempt = getattr(view, 'process_view_exempt', False)
            if not process_view_exempt:
                _process_view = middleware.process_view(request, view)
                if isinstance(_process_view, Response):
                    return _process_view

    def _iter_process_response(self, request, response):
        for middleware in self._middlewares:
            _process_response = middleware.process_response(request, response)
            if isinstance(_process_response, Response):
                response = _process_response
        return response

    def _check_methods(self, methods):
        for method in methods:
            if method.lower() not in self.http_method_names:
                raise Exception('Invalid methods')

    def __call__(self, environ: dict, start_response):
        if 'wsgi.websocket' not in environ.keys():
            return self.wsgi_app(environ, start_response)
        else:
            return self.websocket_app(environ, start_response)
