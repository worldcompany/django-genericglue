from django.db import connections, DEFAULT_DB_ALIAS


def table_exists(table_name, database=DEFAULT_DB_ALIAS):
    """
    Determines if the given table_name exists in the specified database.
    """
    connection = connections[database]
    tables = connection.introspection.table_names()
    converter = connection.introspection.table_name_converter
    return converter(table_name) in tables
