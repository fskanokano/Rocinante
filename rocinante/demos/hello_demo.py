from rocinante import Rocinante, Request

app = Rocinante()


@app.route('/')
def hello(request: Request):
    return 'hello world!'


if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
