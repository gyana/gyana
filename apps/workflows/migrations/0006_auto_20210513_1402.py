# Generated by Django 3.2 on 2021-05-13 14:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0005_auto_20210513_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='kind',
            field=models.CharField(choices=[('input', 'Input'), ('output', 'Output'), ('select', 'Select'), ('join', 'Join'), ('group', 'Group'), ('union', 'Union'), ('sort', 'Sort')], max_length=16),
        ),
        migrations.CreateModel(
            name='SortColumn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ascending', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=300)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sort_columns', to='workflows.node')),
            ],
        ),
    ]
