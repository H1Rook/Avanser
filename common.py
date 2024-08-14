import logging
from contextlib import closing
import pymysql

def log_message(level, message):
    """
    Log messages at different levels.

    :param level: The log level ('INFO' or 'ERROR').
    :param message: The message to log.
    """
    # logging.basicConfig(filename='F:\\pythonProject\\Avanser\\archive_cdr.log', level=logging.INFO,
    #                     format='%(asctime)s %(levelname)s:%(message)s')
    if level == 'INFO':
        logging.info(message)
    elif level == 'ERROR':
        logging.error(message)

def get_connection():
    connection = connection = pymysql.connect(
        host='localhost',
        user='root',
        password='Qaz12345',
        database='edb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection
def execute_query(connection, sql):
    """
    Execute a SQL query and return the results or affected rows.

    :param sql: SQL query string.
    :return: Result of the query as a list of dictionaries for SELECT queries,
             or the number of affected rows for other queries.
    """
    try:
        with closing(connection.cursor()) as cursor:
            cursor.execute(sql)
            connection.commit()
            log_message('INFO', f"Executed query: {sql}")
            if sql.strip().lower().startswith('select'):
                result = cursor.fetchall()  # Return the result for SELECT queries
                return result
            else:
                return cursor.rowcount  # Return the number of affected rows for UPDATE/INSERT/DELETE queries
    except pymysql.MySQLError as e:
        log_message('ERROR', f"SQL execution failed: {e}")
        return None
    finally:
        log_message('INFO', "Database connection closed.")
