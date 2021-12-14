# Generated by Django 3.2.7 on 2021-12-14 08:39

import django.db.models.deletion
from django.db import migrations, models


def forward(apps, schema_editor):
    """Change dashboard to page"""
    Control = apps.get_model("controls", "Control")
    db_alias = schema_editor.connection.alias

    for control in Control.objects.using(db_alias).iterator():
        control.page = control.dashboard.pages.first()
        control.save()


def backward(apps, schema_editor):
    """Change page to dashboad"""
    Control = apps.get_model("controls", "Control")
    db_alias = schema_editor.connection.alias

    for control in Control.objects.using(db_alias).iterator():
        control.dashboard = control.page.dashboard
        control.save()


class Migration(migrations.Migration):

    dependencies = [
        ("dashboards", "0017_page"),
        ("controls", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="control",
            name="page",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="dashboards.page",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="control",
            name="dashboard",
            field=models.ForeignKey(
                null=True,
                to="dashboards.dashboard",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.RunPython(forward, reverse_code=backward),
        migrations.RemoveField(
            model_name="control",
            name="dashboard",
        ),
        migrations.AlterField(
            model_name="control",
            name="page",
            field=models.ForeignKey(
                to="dashboards.page",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
    ]
