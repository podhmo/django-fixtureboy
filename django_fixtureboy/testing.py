import unittest


class CleanHookTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from django_fixtureboy import clearall_hooks
        clearall_hooks()

    def tearDown(self):
        from django_fixtureboy import clearall_hooks
        clearall_hooks()


def get_connection():
    "get default database connection"
    from django.db import connections
    connection = connections['default']
    return connection


def get_cursor(connection):
    "get database cursor from connection"
    return connection.cursor()


def get_style():
    from django.core.management.color import no_style
    return no_style()


def create_table(model):
    connection = get_connection()
    cursor = get_cursor(connection)
    style = get_style()

    sql, references = connection.creation.sql_create_model(
        model, style)
    for statement in sql:
        cursor.execute(statement)

    for f in model._meta.many_to_many:
        create_table(f.rel.through)
