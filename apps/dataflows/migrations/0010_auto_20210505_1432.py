# Generated by Django 3.2 on 2021-05-05 14:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dataflows', '0009_auto_20210505_1312'),
    ]

    operations = [
        migrations.AlterField(
            model_name='node',
            name='kind',
            field=models.CharField(choices=[('input', 'Input'), ('join', 'Join'), ('group', 'Group')], max_length=16),
        ),
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('column', models.CharField(blank=True, max_length=300, null=True)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataflows.node')),
            ],
        ),
        migrations.CreateModel(
            name='Aggregations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('aggregation', models.CharField(choices=[('sum', 'Sum'), ('count', 'Count')], max_length=20)),
                ('column', models.CharField(blank=True, max_length=300, null=True)),
                ('node', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dataflows.node')),
            ],
        ),
    ]
