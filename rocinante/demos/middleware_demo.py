from rocinante import Rocinante, Request, Response
from rocinante.middleware import Middleware
from rocinante.decorator import process_view_exempt

app = Rocinante()


class TestMiddleware(Middleware):

    def process_request(self, request: Request):
        print(request.url)
        request.url = 'process_request'

    def process_view(self, request: Request, view):
        print(request.url)
        request.url = 'process_view'

    def process_response(self, request: Request, response: Response):
        print(request.url)
        response.status = 400


app.add_middleware(Middleware)


@app.route('/')
def index(request):
    print(request.url)
    return 'ok'


@app.route('/exempt')
# use this decorator to exempt from process view
@process_view_exempt
def exempt(request):
    print(request.url)
    return 'ok'


if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
