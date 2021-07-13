# Generated by Django 3.2 on 2021-07-13 22:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("nodes", "0001_initial"),
        ("tables", "0006_auto_20210625_0951"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="table",
                    name="intermediate_node",
                    field=models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="intermediate_node",
                        to="nodes.node",
                    ),
                )
            ],
            # You're reusing an existing table, so do nothing
            database_operations=[],
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="table",
                    name="workflow_node",
                    field=models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="nodes.node",
                    ),
                )
            ],
            # You're reusing an existing table, so do nothing
            database_operations=[],
        ),
    ]
