# Generated by Django 3.2 on 2021-05-26 13:00

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0014_auto_20210526_1054'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addcolumn',
            name='label',
            field=models.CharField(max_length=300, validators=[django.core.validators.RegexValidator('^[a-zA-Z_][0-9a-zA-Z_]*$', 'Only numbers, letters and underscores allowed.')]),
        ),
        migrations.AlterField(
            model_name='node',
            name='kind',
            field=models.CharField(choices=[('input', 'Input'), ('output', 'Output'), ('select', 'Select'), ('join', 'Join'), ('aggregation', 'Aggregation'), ('union', 'Union'), ('sort', 'Sort'), ('limit', 'Limit'), ('filter', 'Filter'), ('edit', 'Edit'), ('add', 'Add'), ('rename', 'Rename')], max_length=16),
        ),
        migrations.CreateModel(
            name='RenameColumn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=300)),
                ('new_name', models.CharField(max_length=300, validators=[django.core.validators.RegexValidator('^[a-zA-Z_][0-9a-zA-Z_]*$', 'Only numbers, letters and underscores allowed.')])),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rename_columns', to='workflows.node')),
            ],
        ),
    ]
