from rocinante import Rocinante, RequestHandler
from mysql.connector.pooling import MySQLConnectionPool

app = Rocinante(__name__)

# mysql config
mysql_config = {
    'pool_size': 2,
    'host': '127.0.0.1',
    'port': 3306,
    'database': 'glow_serializer',
    'user': 'root',
    'password': '123456',
    'pool_reset_session': True
}


class MySQLMixin(object):
    mysql_pool = MySQLConnectionPool(**mysql_config)


class MySQLHandler(RequestHandler, MySQLMixin):

    def get(self):
        connection = self.mysql_pool.get_connection()
        cursor = connection.cursor()
        sql = 'SELECT * FROM user'
        cursor.execute(sql)
        res = cursor.fetchall()

        cursor.close()
        connection.close()

        print(res)

        return res


app.add_handler('/', MySQLHandler)

if __name__ == '__main__':
    app.run('0.0.0.0', 8000, debug=True)
