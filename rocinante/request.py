import json
import traceback

from werkzeug.wrappers import Request as _Request


class Request(_Request):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def set_current_user(self, user):
        self.user = user

    @property
    def remote_port(self):
        return self.environ.get("REMOTE_PORT")

    @property
    def origin(self):
        return self.headers.get('Origin', None)

    def _get_json(self):
        body = self.data
        if body:
            try:
                decode_body = body.decode()
                json_data = json.loads(decode_body)
                if not isinstance(json_data, dict):
                    json_data = {}
            except:
                traceback.print_exc()
                json_data = {}
        else:
            json_data = {}
        return json_data

    @property
    def json(self):
        return self._get_json()
