class DatabaseHelper:
    def __init__(self, local=None, envox=None, central=None, commserver=None):
        self._local = local
        self._envox = envox
        self._central = central
        self._commserver = commserver

    def escape(self, v, db=None):
        if db is None:
            db = self._local or self._envox or self._central or self._commserver

        if not db:
            raise ValueError("Cannot escape without database")

        # Ensure that the value is a string before escaping.
        return db.escape_string(str(v))

    def quote(self, v, db=None):
        if isinstance(v, list):
            return ','.join([self.quote(item, db) for item in v])

        return f"'{self.escape(v, db)}'"

    def _generate_insert_query(self, data, table, db=None):
        # Generate the list of fields for the query from the keys of the data dictionary.
        fields = ','.join([f"`{field}`" for field in data.keys()])

        # Generate the list of values for the query from the values in the data dictionary.
        values = ','.join(
            [self.quote(value, db) if value is not None else 'NULL' for value in data.values()]
        )

        # Generate the complete INSERT query and return it.
        return f"INSERT INTO `{table}` ({fields}) VALUES ({values})"


# Example usage
class MockDB:
    def escape_string(self, value):
        # Simple escape logic for demonstration. Ensure value is a string.
        return value.replace("'", "\\'")


db = MockDB()
helper = DatabaseHelper(local=db)

data = {
    'name': "O'Reilly",
    'age': 30,
    'email': "john@example.com"
}
table = 'users'

query = helper._generate_insert_query(data, table)
print(query)  # Output: INSERT INTO `users` (`name`,`age`,`email`) VALUES ('O\\'Reilly',30,'john@example.com')
