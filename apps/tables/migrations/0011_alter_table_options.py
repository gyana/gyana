# Generated by Django 3.2.5 on 2021-08-13 08:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0010_alter_table_num_rows'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='table',
            options={'ordering': ('-created',)},
        ),
    ]
