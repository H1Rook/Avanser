import logging
from contextlib import closing
import pymysql

# Configure logging at the start of the script
logging.basicConfig(
    filename='F:\\pythonProject\\Avanser\\archive_cdr.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def log_message(level, message):
    """
    Log messages at different levels.

    :param level: The log level ('INFO' or 'ERROR').
    :param message: The message to log.
    """
    if level == 'INFO':
        logging.info(message)
    elif level == 'ERROR':
        logging.error(message)

def get_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='Qaz12345',
        database='edb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_history_connection():
    return pymysql.connect(
        host='localhost',
        port=3307,
        user='root',
        password='Qaz12345',
        database='edb',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def execute_query(conn, sql):
    """
    Execute a SQL query and return the results or affected rows.

    :param conn: The database connection object.
    :param sql: SQL query string.
    :return: Result of the query as a list of dictionaries for SELECT queries,
             or the number of affected rows for other queries.
    """
    try:
        with closing(conn.cursor()) as cursor:
            cursor.execute(sql)
            conn.commit()
            log_message('INFO', f"Executed query: {sql}")
            if sql.strip().lower().startswith('select'):
                return cursor.fetchall()  # Return results for SELECT queries
            else:
                return cursor.rowcount  # Return affected rows count for other queries
    except pymysql.MySQLError as e:
        log_message('ERROR', f"SQL execution failed: {e}")
        return None
    finally:
        log_message('INFO', "Database connection closed.")
