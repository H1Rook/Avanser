from common import execute_query, get_history_connection
from ArchiveCdr import ArchiveCdr
archiver = ArchiveCdr()

sql = "show databases"

dbs = archiver._query_history_db(sql)
print(dbs)
