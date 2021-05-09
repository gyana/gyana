# Generated by Django 3.2 on 2021-05-08 02:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("dataflows", "0015_auto_20210508_0154"),
    ]

    operations = [
        migrations.RenameField(
            model_name="node",
            old_name="input_dataset",
            new_name="input_table",
        ),
        migrations.AddField(
            model_name="node",
            name="dataflow",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="dataflows.dataflow",
            ),
            preserve_default=False,
        ),
    ]
