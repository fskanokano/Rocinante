from rocinante import Rocinante
from rocinante.middleware import CORSMiddleware

app = Rocinante()

app.add_middleware(CORSMiddleware)

if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
