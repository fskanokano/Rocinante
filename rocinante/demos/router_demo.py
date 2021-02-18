from rocinante import Rocinante, RequestHandler, Router, Request, Url

app = Rocinante(__name__)


# other way to register handler
class HelloHandler(RequestHandler):

    def get(self, request: Request):
        print(request.url)
        return 'get!'

    def post(self, request: Request):
        print(request.url)
        return 'post!'


app.add_handler('/', HelloHandler)

# use router
router = Router()

# different way to register handler

# 1
""""""


@router.route('/test', methods=['GET', 'POST'])
def router_handler(request: Request):
    if request.method == 'GET':
        return 'get!'
    elif request.method == 'POST':
        return 'post!'


""""""

# 2
""""""


class RouterHandler2(RequestHandler):

    def get(self):
        return 'get!'

    def post(self):
        return 'post!'


router.add_handler('/test2', RouterHandler2)

""""""

# 3
""""""


class RouterHandler3(RequestHandler):

    def get(self):
        return 'get!'

    def post(self):
        return 'post!'


urlpatterns = [
    Url('/test3', RouterHandler3)
]

router.add_urlpatterns(urlpatterns)

""""""

# include router
app.include_router(router, prefix='/router')

if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
