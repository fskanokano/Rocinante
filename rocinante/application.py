from inspect import isfunction
from typing import Callable
from collections import Iterable

from werkzeug import run_simple, Response
from werkzeug.exceptions import NotFound
from werkzeug.routing import Map, Rule

from .request import Request
from .response import NotFoundResponse, MethodNotAllowedResponse, JSONResponse
from .config import Config
from .cache import HandlerLRUCache


class Rocinante(object):
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    url_map = Map()

    _middlewares = []

    _config = Config

    _mounted_wsgi_apps = {}

    _cache = HandlerLRUCache()

    def __init__(self, handler_cache_capacity: int = 128):
        self.handler_cache_capacity = handler_cache_capacity

    def __call__(self, environ: dict, start_response):
        request = Request(environ)

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

                return NotFoundResponse()(environ, start_response)

        # handle fbv
        if isfunction(endpoint):
            allow_methods = endpoint.allow_methods
            if request.method not in allow_methods:
                return MethodNotAllowedResponse()(environ, start_response)

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
                    return MethodNotAllowedResponse()(environ, start_response)
                else:
                    return NotFoundResponse()(environ, start_response)

            # iterate process_view of middlewares
            _process_view = self._iter_process_view(request, method)
            if isinstance(_process_view, Response):
                return _process_view(environ, start_response)

            # reload the handler to keep the change of request
            handler.reload_request(request)

            response = method(**kwargs)

        # process object not the instance of Response class
        if not isinstance(response, Response):
            if isinstance(response, tuple) and isinstance(response[1], int):
                response = self._make_response(*response)
            elif isinstance(response, Iterable):
                response = self._make_response(response)

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
            raise Exception('Invalid prefix.')

        if not callable(app):
            raise Exception('Invalid wsgi application.')

        self._mounted_wsgi_apps[path] = app

    def run(self, host, port, *, debug: bool = False):
        run_simple(host, port, self, use_debugger=debug, use_reloader=debug)

    @staticmethod
    def _process_environ(environ, request, path):
        wsgi_app_url_location = len(path)
        wsgi_app_url = request.path[wsgi_app_url_location:]
        environ['PATH_INFO'] = wsgi_app_url
        environ['REQUEST_URI'] = wsgi_app_url
        environ['RAW_URI'] = wsgi_app_url
        return environ

    @staticmethod
    def _make_response(content, status=None):
        if isinstance(content, Iterable):
            return JSONResponse(content, status)

    def _execute_startup_event(self):
        for event_dict in self.startup_event:
            event = event_dict['event']
            kwargs = event_dict['kwargs']
            event(**kwargs)

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
