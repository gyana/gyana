# Generated by Django 3.2.7 on 2021-11-05 13:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('nodes', '0014_node_has_been_saved'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tables', '0014_auto_20210928_1459'),
    ]

    operations = [
        migrations.CreateModel(
            name='Export',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('gcs_path', models.CharField(max_length=255)),
                ('status', models.CharField(choices=[('running', 'Running'), ('table_created', 'Table created'), ('exported', 'Exported')], default='running', max_length=16)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('integration_table', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exports', to='tables.table')),
                ('node', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='exports', to='nodes.node')),
            ],
            options={
                'ordering': ('-updated',),
                'abstract': False,
            },
        ),
    ]
