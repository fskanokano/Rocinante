from rocinante import Rocinante, RequestHandler, Request, RequestHeaders, RequestCookies, RequestForm, RequestFiles, \
    RequestArgs, RequestJSON, RequestBody

app = Rocinante(__name__)


class ArgumentsHandler(RequestHandler):

    # get all request arguments
    def get(
            self,
            request: Request,
            headers: RequestHeaders,
            cookies: RequestCookies,
            form: RequestForm,
            files: RequestFiles,
            args: RequestArgs,
            json: RequestJSON,
            body: RequestBody
    ):
        print(request)
        print(headers)
        print(cookies)
        print(form)
        print(files)
        print(args)
        print(json)
        print(body)

        return 'all request arguments'

    # get specific request arguments
    def post(
            self,
            cookies: RequestCookies,
            headers: RequestHeaders,
            body: RequestBody
    ):
        print(cookies)
        print(headers)
        print(body)

        return 'specific request arguments'


class PathHandler(RequestHandler):

    def get(self, request: Request, path_id, headers: RequestHeaders):
        print(request)
        print(path_id)
        print(headers)

        return 'ok'


app.add_handler('/arguments', ArgumentsHandler)
app.add_handler('/path/<path_id>', PathHandler)

if __name__ == '__main__':
    app.run()
