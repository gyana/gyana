# Generated by Django 3.2 on 2021-07-13 12:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0039_auto_20210713_1200'),
    ]

    operations = [
        migrations.AlterField(
            model_name='windowcolumn',
            name='group_by',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='windowcolumn',
            name='order_by',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
