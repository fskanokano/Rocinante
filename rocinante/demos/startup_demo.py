from rocinante import Rocinante

app = Rocinante()


@app.startup()
def start():
    print('startup!')


if __name__ == '__main__':
    app.run('0.0.0.0', 8000)
