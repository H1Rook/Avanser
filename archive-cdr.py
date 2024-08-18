#!/usr/bin/python3
"""
AVANSER - Archive CDR based on the flush flag into local DNIS table.
   Last modified: 20 Jun 2018
      Coded by: James Fletcher <james.f@avanser.com.au>
       Support: AA-23 or later

        Crontab: 0 1  *   *  * root /avanser/daemons/archive_cdr.py >> /avanser/log/archive_cdr.log 2>&1
 Check last run: cat /avanser/run/archive_cdr.timestamp
         Run on: edb1, kdb1, sgcl, ucs1, all_db
"""

import sys
import re
import logging

from ArchiveCdr import ArchiveCdr
from common import execute_query, get_connection, log_message

import pymysql

# Configuration and database connection setup
CONF = {
    'path': '/avanser/',
    'node': 'edb1'
}

# Determine environment based on node
environment = 'test'

def main():
    """
    Main function to archive CDR based on the flush flag into local DNIS table.
    """
    # Establish connections to local and central databases
    # central_db_conn = get_db_connection('central')

    log_message('INFO', 'Script started')
    connection = get_connection()
    log_message("INFO", 'Connected to MySQL database')
    # Get a list of DNIS numbers that need to be flushed [start]
    sql = "SELECT `dn_number` AS `number` FROM `dnis` WHERE `dn_flushCdr` = 'Y'"

    numbers = execute_query(connection, sql)

    if not numbers:
        log_message('INFO', 'No DNIS records need to be flushed.')
        connection.close()


    count_numbers = len(numbers)
    log_message('INFO', f"{count_numbers} DNIS records found that need to be flushed.")
    # Get a list of DNIS numbers that need to be flushed [stop]

    # Initialise the archiver class. Terminate the script if it throws an error.
    try:
        archiver = ArchiveCdr()
    except Exception as e:
        log_message('ERROR', e)

    # Loop through each number and archive all of the associated CDR records [start]
    record_count = 0
    for number in numbers:
        dnis = number['number']
        log_message("INFO", f"Processing number: {dnis}")

        # Get the BNUM associated with this DNIS from the inbound table [start]
        sql = f"SELECT `Number` AS `bnum` FROM `inbound` WHERE `Terminating_No` = '{dnis}'"
        bnum = execute_query(connection, sql)
        if not bnum:
            log_message('INFO', [dnis, 'No BNUM found for DNIS'])
            update_dnis_flush(connection, dnis)  # Prevent re-trying this record every time the script runs
            continue
            # There should only be one record for each DNIS, so just extract the BNUM from the "first" record.

        bnum = bnum[0]['bnum']

        table_queries = {
            'cdr': f"`cd_bnum` = '{bnum}' OR (`cd_clientId` = 5000 AND `cd_dnis` = '{dnis}')",
            'cdr_sms': f"`cs_from` = '{bnum}' OR `cs_to` = '{bnum}'"
        }

        for table_name, query in table_queries.items():
            if not archiver.set_table_query(table_name, query):
                print('ERR', f"Table not configured to be archived: {table_name}")

        # Run the archiver process using the query conditions assigned above.
        records_archived = archiver.archive()
        if not records_archived:
            log_message('ERR', [dnis, bnum, 'Unable to archive records'])
            # If the archiver failed, log a message and skip to the next number.
            continue
        # Update the DNIS record for this number to disable the flushCdr flag.
        record_count += records_archived
        update_dnis_flush(connection, dnis)

        # If this number exists in the inventory_recycle table, set the archive_completed flag.
        update_inventory_recycle(connection, dnis)

    log_message('INFO', f"{record_count} records archived across {count_numbers} numbers.")
    # Loop through each number and archive all of the associated CDR records [stop]
    connection.close()


def update_inventory_recycle(connection, number):
    """
    Check if the given number exists in the inventory_recycle table, matched by DNIS.
    If so, set the archive_completed flag to 1.

    :param connection: MySQL connection object.
    :param number: BNUM or DNIS.
    """
    sql = f"SELECT `id` FROM `inventory_recycle` WHERE `dnis` = '{number}' AND `archive_completed` = 0"
    records = execute_query(connection, sql)

    if records:
        for record in records:
            sql = f"UPDATE `inventory_recycle` SET `archive_completed` = 1 WHERE `id` = {record['id']}"
            update = execute_query(connection, sql)
            if not update:
                log_message('ERROR', f"Unable to update inventory_recycle, ID: {record['id']}")


def update_dnis_flush(connection, dnis):
    """Update the DNIS record to disable the flushCdr flag."""

    sql = f"update dnis set dn_flushCdr = 'N' where dn_number = '{dnis}'"
    log_message('INF', f"Executing SQL: {sql}")
    update = execute_query(connection, sql)
    if not update:
        log_message('ERR', f"Failed to update flushCdr for DNIS: {dnis}")
    else:
        log_message('INFO', f"Updated flushCdr for DNIS: {dnis}")




if __name__ == "__main__":
    main()
