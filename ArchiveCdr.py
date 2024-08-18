import sqlite3
import datetime

from common import get_connection, execute_query, get_history_connection


class ArchiveCdr:
    """
    Class to handle archiving of CDR records and associated tables.
    """

    # Static list of tables and associated tables
    _tables = {
        "cdr": {
            "id_field": "cd_id",
            "query": "None"
        },
        "cdr_sms": {
            "id_field": "cs_id",
            "query": "None"
        },
    }

    _associated_tables = {
        "cdr_adwords": {
            "id_field": "ca_id",
            "link_field": "ca_cdrId",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
        "cdr_chats": {
            "id_field": "cc_id",
            "link_field": "cc_userUniqueid",
            "link_field_other": "cd_uniqueid",
            "linked_table": "cdr",
        },
        "cdr_doubleclick": {
            "id_field": "cdc_id",
            "link_field": "cdc_cdrId",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
        "cdr_evaluations": {
            "id_field": "id",
            "link_field": "cq_cdrId",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
        "cdr_inputs": {
            "id_field": "ci_id",
            "link_field": "ci_uniqueId",
            "link_field_other": "cd_uniqueid",
            "linked_table": "cdr",
        },
        "cdr_notes": {
            "id_field": "cdh_id",
            "link_field": "cdr_id",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
        "cdr_salesforce": {
            "id_field": "cs_id",
            "link_field": "cs_cdrId",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
        "cdr_transcript": {
            "id_field": "ctr_id",
            "link_field": "ctr_cdrId",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
        "cdr_webhits": {
            "id_field": "cwh_id",
            "link_field": "cwh_cdrId",
            "link_field_other": "cd_id",
            "linked_table": "cdr",
        },
    }

    def __init__(self):
        """
        Constructor
        """
        self._structure_updated = []
        self._query_limit = 100000
        self._records_archived = 0

    def set_table_query(self, table_name, query):
        """
        Set the query condition to use for the given table.

        :param table_name: Name of the table
        :param query: Query condition to be used
        :return: Boolean indicating success or failure
        """
        if table_name not in self._tables:
            return False

        self._tables[table_name]['query'] = query
        return True

    def archive(self):
        """
        Archives the records in each configured table, based on the query condition in the _tables property.
        The query for each table must be set by calling the set_table_query() method before calling this method.

        :return: The total number of records archived, across all tables. False if an error is encountered.
        """
        self._records_archived = 0

        # Loop through each table and archive the records based on the configured query condition
        for table_name, table_details in self._tables.items():
            if table_details.get('query') is None:
                print(f"Query not set for table: {table_name}")
                return False

            if not self._copy_records(table_name, table_details['query'], table_details['id_field']):
                return False

        return self._records_archived

    def _copy_records(self, table_name, where_condition, id_field, is_associated_table=False):
        """
        Archive the records for the given table, based on the given query condition.

        :param table_name: Name of the table
        :param where_condition: Query condition to be used
        :param id_field: Name of the field used to match the record in the original table for deletion
        :param is_associated_table: Boolean indicating if the table is an associated table
        :return: Boolean indicating success or failure
        """
        # Check if the structure of this table needs to be updated [start]
        if table_name not in self._structure_updated:
            # if not self._update_structure(table_name):
            #     return False
            self._structure_updated.append(table_name)

        while True:
            sql = f"SELECT * FROM {table_name} WHERE {where_condition} LIMIT 0, {self._query_limit}"
            records = self._query_local_db(sql)

            if records is None:
                print(f"Error retrieving records from table: {table_name}- Possible condition error.")
                return False

            number_records = len(records)
            if not records or number_records == 0:
                break

            for record in records:
                if not self._copy_record(record, table_name, id_field):
                    return False

            if number_records < self._query_limit:
                break

        return True

    def _copy_record(self, record, table_name, id_field):
        """
        Insert the given record into the given table in the history server, and delete it from the given table in the local server.

        :param record: Record to be copied
        :param table_name: Name of the table
        :param id_field: Name of the field used to match the record in the original table for deletion
        :return: Boolean indicating success or failure
        """
        sql = self._generate_insert_query(record, table_name)

        if not self._query_history_db(sql):
            print(f"Unable to insert record into table: {table_name} (ID: {record[id_field]})")
            return False
    # Process any "associated tables" for the given table [start]
        if table_name in self._associated_tables:
            for assoc_table_name, table_details in self._associated_tables[table_name].items():
                link_value = self._database_quote(record[table_details['link_field_other']])
                assoc_condition = f"`{table_details['link_field']}` = {link_value}"

                if not self._copy_records(assoc_table_name, assoc_condition, table_details['id_field'], True):
                    return False

        record_id = self._database_quote(record[id_field])
        sql = f"DELETE FROM `{table_name}` WHERE `{id_field}` = {record_id} LIMIT 1"
        if not self._query_local_db(sql):
            print(f"Unable to delete record from table: {table_name} (ID: {record[id_field]})")
            return False

        self._records_archived += 1
        return True

    def _update_structure(self, table_name):
        """
        Check if any fields in the given table on the history server are different from the local server,
        and update the structure accordingly.

        :param table_name: Name of the table
        :return: Boolean indicating success or failure
        """
        sql = f"SHOW TABLES LIKE '{table_name}'"
        table_exists = bool(self._query_history_db(sql))

        sql = f"DESCRIBE `{table_name}`"
        local_structure = self._query_local_db(sql)
        history_structure = self._query_history_db(sql) if table_exists else []

        if local_structure is False or history_structure is False:
            print(f"Unable to retrieve table structure: {table_name}")
            return False

        structure_changes = self._check_structure_changes(local_structure, history_structure, table_exists)

        if structure_changes:
            structure_changes = ', '.join(structure_changes)
            sql = f"ALTER TABLE `{table_name}` {structure_changes}" if table_exists else f"CREATE TABLE IF NOT EXISTS `{table_name}` ({structure_changes}) ENGINE=MyISAM"
            print(f"Updating table structure: {table_name} - {sql}")
            if not self._query_history_db(sql):
                print(f"Unable to update/create table: {table_name}")
                return False

        return True

    def _check_structure_changes(self, local_structure, history_structure, table_exists):
        """
        Given arrays containing the structure for a given table in both the local and history servers,
        checks for differences between the structures, and returns an array of SQL statements to update the
        structure of the history server to match the local server.

        :param local_structure: Structure of the local table
        :param history_structure: Structure of the history table
        :param table_exists: Boolean indicating if the table exists
        :return: List of SQL statements to update the structure
        """
        structure_changes = []

        previous_field = ''
        for local_field in local_structure:
            action = 'create'

            for history_field in history_structure:
                if local_field['Field'].lower() == history_field['Field'].lower():
                    action = 'skip'
                    if any(local_field[attr] != history_field[attr] for attr in ['Field', 'Type', 'Null']):
                        action = 'edit'
                        local_field['Prev_Name'] = history_field['Field']
                    break

            if action != 'skip':
                structure_changes.append(
                    self._generate_structure_change_statement(local_field, action, table_exists, previous_field))

            previous_field = local_field['Field']

        return structure_changes

    # Placeholder methods for database interactions (to be implemented as needed)
    def _query_local_db(self, sql):
        connection = get_connection()
        return execute_query(connection, sql)

    def _query_history_db(self, sql):
        history_connection = get_history_connection()
        return execute_query(history_connection, sql)

    def _generate_insert_query(self, record, table_name):

        fields = ','.join(f"`{field}`" for field in record.keys())
        values = ','.join(
            'NULL' if value is None else f"'{value}'" if isinstance(value,
                                                                    (str, datetime.date, datetime.datetime)) else str(
                value)
            for value in record.values()
        )

        return f"INSERT INTO `{table_name}` ({fields}) VALUES({values})"

    def _database_quote(self, value):
        """
    Escapes and quotes the input value for safe use in SQL queries.

    :param value: The value to be quoted and escaped.
    :return: The safely quoted and escaped value.
    """
        if value is None:
            return 'NULL'

        if isinstance(value, (int, float)):
            # If it's a number, return as is (no quotes)
            return str(value)

        # Escape special characters in strings (e.g., quotes)
        if isinstance(value, str):
            value = value.replace("\\", "\\\\")  # Escape backslashes
            value = value.replace("'", "\\'")    # Escape single quotes
            value = value.replace('"', '\\"')    # Escape double quotes

            # Wrap the value in single quotes for SQL
            return f"'{value}'"

        # If it's another type, convert it to string and quote
        return f"'{str(value)}'"

    def _generate_structure_change_statement(self, field_data, action, table_exists, previous_field):
        pass
