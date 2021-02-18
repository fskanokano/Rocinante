from rocinante import Rocinante, Render, Request, RequestHeaders

app = Rocinante(__name__)


@app.route('/')
def index(request: Request, headers: RequestHeaders):
    url = request.url

    return Render(
        # template path
        'templates/index.html',
        status=400,
        # pass the context to template
        url=url,
        headers=headers
    )


if __name__ == '__main__':
    app.run()
