import sys
import re
import logging
from contextlib import closing
from common import get_connection, execute_query, log_message
from ArchiveCdr import ArchiveCdr

# Configuration and database connection setup
CONF = {
    'path': '/avanser/',
    'node': 'edb1'
}

# Determine environment based on node
environment = 'test'

# 56134 5 4
#'+61-1300989659'

#
# if CONF['node'] in ['webdev', 'devsql', 'edb2'] or re.search(r'sandbox|devcs', CONF['node']):
#     environment = 'test'

def update_dnis_flush(connection, dnis):
    """Update the DNIS record to disable the flushCdr flag."""
    sql = f"update dnis set dn_flushCdr = 'N' where dn_number = '{dnis}'"
    print('INF', f"Executing SQL: {sql}")

    update = execute_query(connection, sql)

    if not update:
        print('ERR', f"Failed to update flushCdr for DNIS: {dnis}")
    else:
        print('INFO', f"Updated flushCdr for DNIS: {dnis}")

    """
    Main function to archive CDR based on the flush flag into local DNIS table.
    """

# print('INFO', 'Script started')
# connection = get_connection()
# print("INFO", 'Connected to MySQL database')
# # Get a list of DNIS numbers that need to be flushed [start]
# sql = "SELECT `dn_number` AS `number` FROM `dnis` WHERE `dn_flushCdr` = 'Y'"
#
# numbers = execute_query(connection, sql)
#
# if not numbers:
#     print('INFO', 'No DNIS records need to be flushed.')
#     connection.close()
#
#
# count_numbers = len(numbers)
# print('INFO', f"{count_numbers} DNIS records found that need to be flushed.")
# # Get a list of DNIS numbers that need to be flushed [stop]
#
# # Initialise the archiver class. Terminate the script if it throws an error.
# try:
#     archiver = ArchiveCdr()
# except Exception as e:
#     print('ERROR', e)
#
# # Loop through each number and archive all of the associated CDR records [start]
# record_count = 0
# for number in numbers:
#     dnis = number['number']
#     print("INFO", f"Processing number: {dnis}")
#
#     # Get the BNUM associated with this DNIS from the inbound table [start]
#     sql = f"SELECT `Number` AS `bnum` FROM `inbound` WHERE `Terminating_No` = '{dnis}'"
#     bnum = execute_query(connection, sql)
#     if not bnum:
#         print('INFO', [dnis, 'No BNUM found for DNIS'])
#         update_dnis_flush(connection, dnis)  # Prevent re-trying this record every time the script runs
#         continue
#         # There should only be one record for each DNIS, so just extract the BNUM from the "first" record.
#
#     bnum = bnum[0]['bnum']
#
#     table_queries = {
#         'cdr': f"`cd_bnum` = '{bnum}' OR (`cd_clientId` = 5000 AND `cd_dnis` = '{dnis}')",
#         'cdr_sms': f"`cs_from` = '{bnum}' OR `cs_to` = '{bnum}'"
#     }
#
#     for table_name, query in table_queries.items():
#         if not archiver.set_table_query(table_name, query):
#             print('ERR', f"Table not configured to be archived: {table_name}")
#
#     # Run the archiver process using the query conditions assigned above.
#     records_archived = False
#     if not records_archived:
#         print('ERR', [dnis, bnum, 'Unable to archive records'])
#         # If the archiver failed, log a message and skip to the next number.
#         continue
#     # Update the DNIS record for this number to disable the flushCdr flag.
#     record_count += records_archived
#     update_dnis_flush(connection, dnis)
#
#     # If this number exists in the inventory_recycle table, set the archive_completed flag.
#     # update_inventory_recycle(connection, dnis)
# update_dnis_flush(connection, '+61-0291913204')
# print('INFO', f"{record_count} records archived across {count_numbers} numbers.")
# connection.close()
#
