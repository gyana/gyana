# Generated by Django 3.2.7 on 2021-11-23 13:44

import dirtyfields.dirtyfields
import django.db.models.deletion
from django.db import migrations, models
from model_clone import CloneMixin


class Migration(migrations.Migration):

    dependencies = [
        ("nodes", "0017_alter_node_kind"),
        ("columns", "0010_rename_functions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ConvertColumn",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                ("column", models.CharField(help_text="Select column", max_length=300)),
                (
                    "target_type",
                    models.CharField(
                        choices=[
                            ("text", "Text"),
                            ("int", "Integer"),
                            ("float", "Decimal"),
                            ("bool", "Bool"),
                            ("date", "Date"),
                            ("time", "Time"),
                            ("timestamp", "Datetime"),
                        ],
                        help_text="Select type to convert to",
                        max_length=16,
                    ),
                ),
                (
                    "node",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="convert_columns",
                        to="nodes.node",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
            bases=(
                dirtyfields.dirtyfields.DirtyFieldsMixin,
                CloneMixin,
                models.Model,
            ),
        ),
    ]
