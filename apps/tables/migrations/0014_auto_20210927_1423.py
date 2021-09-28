# Generated by Django 3.2.7 on 2021-09-27 14:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nodes', '0013_auto_20210927_1423'),
        ('tables', '0013_auto_20210822_0024'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='cache_node',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='cache_node', to='nodes.node'),
        ),
        migrations.AlterField(
            model_name='table',
            name='source',
            field=models.CharField(choices=[('integration', 'Integration'), ('workflow_node', 'Workflow node'), ('intermediate_node', 'Intermediate node'), ('cache_node', 'Cache node')], max_length=18),
        ),
    ]
