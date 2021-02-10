from rocinante import Rocinante
from flask import Flask

app = Rocinante()

flask_app = Flask(__name__)


@flask_app.route('/index')
def flask_test():
    return 'flask_index!'


app.mount_wsgi_app(flask_app, path='/flask')

if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
