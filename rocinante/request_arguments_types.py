from werkzeug.datastructures import EnvironHeaders, ImmutableMultiDict

from .request import Request


class RequestHeaders(EnvironHeaders):
    pass


class RequestCookies(ImmutableMultiDict):
    pass


class RequestForm(ImmutableMultiDict):
    pass


class RequestFiles(ImmutableMultiDict):
    pass


class RequestArgs(ImmutableMultiDict):
    pass


class RequestJSON(dict):
    pass


class RequestBody(bytes):
    pass


SUPPORT_ARGUMENTS_MAPPING = {
    Request: 'request',
    RequestHeaders: 'headers',
    RequestCookies: 'cookies',
    RequestForm: 'form',
    RequestFiles: 'files',
    RequestArgs: 'args',
    RequestJSON: 'json',
    RequestBody: 'data'
}
