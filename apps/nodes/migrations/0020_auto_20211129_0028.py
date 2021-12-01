# Generated by Django 3.2.7 on 2021-11-29 00:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("nodes", "0019_auto_20211129_0027"),
    ]

    operations = [
        migrations.RunSQL(
            """
        UPDATE nodes_edge
        SET created = nodes_node.created,
            updated = nodes_node.updated
        FROM nodes_node
        WHERE nodes_edge.child_id = nodes_node.id
        """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
