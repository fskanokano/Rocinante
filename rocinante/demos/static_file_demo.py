from rocinante import Rocinante
from rocinante.handler import StaticFileHandler

app = Rocinante()

app.add_static_file_handler(
    handler=StaticFileHandler,
    prefix='/images',
    file_dir='images'
)

app.add_static_file_handler(
    handler=StaticFileHandler,
    prefix='/videos',
    file_dir='videos'
)

if __name__ == '__main__':
    app.run()
