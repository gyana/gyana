# Generated by Django 3.2.5 on 2021-08-11 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("connectors", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DELETE FROM connectors_connector
            WHERE service IS NULL
                OR fivetran_id IS NULL
                OR schema IS NULL
            ;
        """,
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
