from django.db import connection


def _create_duplicate_database_with_template(target: str, template: str):

    db_params = {
        "target": connection.ops.quote_name(target),
        "template": connection.ops.quote_name(template),
    }

    with connection.cursor() as cursor:
        cursor.execute("DROP DATABASE IF EXISTS %(target)s WITH (FORCE)" % db_params)
        cursor.execute(
            "CREATE DATABASE %(target)s WITH TEMPLATE %(template)s;" % db_params
        )


def create_testdb_from_template():

    test_database_name = connection.creation._get_test_db_name()
    template_database_name = f"{test_database_name}_template"

    _create_duplicate_database_with_template(test_database_name, template_database_name)


def create_template_from_testdb():

    test_database_name = connection.creation._get_test_db_name()
    template_database_name = f"{test_database_name}_template"

    _create_duplicate_database_with_template(template_database_name, test_database_name)
