from werkzeug import Response
from rocinante import Rocinante, Request


class MyRequest(Request):

    @property
    def my_property(self):
        return 'my request!'


class MyResponse(Response):

    @property
    def my_property(self):
        return 'my response!'


app = Rocinante(
    __name__,
    request_class=MyRequest,
    response_class=MyResponse
)


@app.route('/')
def index(request: MyRequest):
    print(request.my_property)
    response = MyResponse('ok')
    print(response.my_property)
    return response


if __name__ == '__main__':
    app.run()
