from rocinante import Rocinante, RequestHandler
from mysql.connector.pooling import MySQLConnectionPool

app = Rocinante()


# config class
class MySQLConfig(object):
    pool_size = 2
    host = '127.0.0.1'
    port = 3306
    database = 'Rocinante'
    user = 'root'
    password = '123456'
    pool_reset_session = True


# load config to app
app.load_config('mysql', MySQLConfig)


class MySQLMixin(object):
    def __init__(self, application: Rocinante):
        # get config from app
        mysql_config = application.get_config('mysql')
        self.mysql_pool = MySQLConnectionPool(**mysql_config)


class MySQLHandler(RequestHandler, MySQLMixin):

    def get(self):
        connection = self.mysql_pool.get_connection()
        cursor = connection.cursor()
        sql = 'SELECT * FROM user'
        cursor.execute(sql)
        res = cursor.fetchall()

        connection.close()
        cursor.close()

        return res


app.add_handler('/', MySQLHandler)

if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True)
