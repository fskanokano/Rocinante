import json
from typing import Type
from inspect import isfunction
from typing import Callable
from collections import Iterable

from werkzeug import run_simple, Response, Request as WerkzeugRequest
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map, Rule

from .request import Request
from .config import Config
from .cache import HandlerLRUCache


class Rocinante(object):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    url_map = Map()

    _middlewares = []

    _config = Config

    _mounted_wsgi_apps = {}

    _cache = HandlerLRUCache()

    def __init__(
            self,
            request_class: Type[WerkzeugRequest] = Request,
            response_class: Type[Response] = Response,
            json_response_class: Type[Response] = None,
            not_found_response_class: Type[Response] = None,
            method_not_allowed_response_class: [Response] = None,
            handler_cache_capacity: int = 128
    ):
        """
        accept subclass of werkzeug.Request or subclass of werkzeug.Response
        """

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

    def __call__(self, environ: dict, start_response):
        request = self.request_class(environ)

        # iterate process_request of middlewares
        _process_request = self._iter_process_request(request)
        if isinstance(_process_request, Response):
            return _process_request(environ, start_response)

        # try to get cached handler
        cached_dict = self._cache.get(request.path)

        # success get cached endpoint
        if cached_dict is not None:
            endpoint = cached_dict['endpoint']
            kwargs = cached_dict['kwargs']

        # cannot get cached handler
        else:

            # get adapter
            adapter = self.url_map.bind_to_environ(environ)

            # try to match the endpoint and kwargs
            try:
                endpoint, kwargs = adapter.match()

                # set endpoint to cache
                self._cache.set(request.path, {'endpoint': endpoint, 'kwargs': kwargs})

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
            allow_methods = endpoint.allow_methods
            if request.method not in allow_methods:
                return self.method_not_allowed_response_class()(environ, start_response)

            # iterate process_view of middlewares
            _process_view = self._iter_process_view(request, endpoint)
            if isinstance(_process_view, Response):
                return _process_view(environ, start_response)

            response = endpoint(request, **kwargs)

        # handle cbv
        else:
            handler = endpoint(application=self, request=request)

            if cached_dict is not None:
                # reload the request to cbv
                handler.reload_request(request)

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

            # reload the handler to keep the change of request
            handler.reload_request(request)

            response = method(**kwargs)

        # process object not the instance of Response class
        if not isinstance(response, Response):
            response = self._process_response(response)

        # iterate process_response of middlewares
        response = self._iter_process_response(request, response)

        # call response object and return it
        return response(environ, start_response)

    def route(self, rule, *, methods=['GET']):
        self._check_methods(methods)

        def wrapper(fbv):
            fbv.allow_methods = methods
            self.url_map.add(Rule(rule, endpoint=fbv))
            return fbv

        return wrapper

    def add_handler(self, rule, handler):
        self.url_map.add(Rule(rule, endpoint=handler))

    @staticmethod
    def startup():
        def wrapper(event):
            event()
            return event

        return wrapper

    def include_router(self, router, *, prefix: str = None):
        for rule in router.rules:
            if prefix is None:
                self.url_map.add(rule)
            else:
                self.url_map.add(Rule(prefix + rule.rule, endpoint=rule.endpoint))

    def add_middleware(self, middleware, **kwargs):
        self._middlewares.append(middleware(**kwargs))

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

    def run(self, host: str = '0.0.0.0', port: int = 8000, *, debug: bool = True):
        run_simple(host, port, self, use_debugger=debug, use_reloader=debug)

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
        else:
            if not isinstance(response, Iterable):
                raise Exception('Invalid Iterable object.')
            processed_response = self._make_response(response)
        return processed_response

    @staticmethod
    def _check_request_class(*request_classes):
        for request_class in request_classes:
            if not issubclass(request_class, WerkzeugRequest):
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
