# Generated by Django 3.2 on 2021-06-25 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0008_auto_20210610_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='widget',
            name='kind',
            field=models.CharField(choices=[('text', 'Text'), ('table', 'Table'), ('column2d', 'Column'), ('line', 'Line'), ('pie2d', 'Pie'), ('area2d', 'Area'), ('doughnut2d', 'Donut'), ('scatter', 'Scatter')], default='column2d', max_length=32),
        ),
    ]
