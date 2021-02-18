from rocinante import Rocinante
from flask import Flask
from fastapi import FastAPI

app = Rocinante(__name__)

flask_app = Flask(__name__)

fastapi_app = FastAPI()


@flask_app.route('/index')
def flask_index():
    return 'flask index!'


@fastapi_app.get('/index')
def fastapi_index():
    return 'fastapi index!'


app.mount_wsgi_app(flask_app, path='/flask')

app.mount_asgi_app(fastapi_app, path='/fastapi')

if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
