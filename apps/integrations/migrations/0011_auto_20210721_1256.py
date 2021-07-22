# Generated by Django 3.2 on 2021-07-21 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0010_alter_integration_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integration',
            name='fivetran_id',
            field=models.TextField(help_text='ID of the connector in Fivetran, crucial to link this Integration to the Fivetran connector', null=True),
        ),
        migrations.AlterField(
            model_name='integration',
            name='schema',
            field=models.TextField(help_text='The schema name under which Fivetran saves the data in BigQuery. It also is the name of the schema maintained by Fivetran in their systems.', null=True),
        ),
        migrations.AlterField(
            model_name='integration',
            name='service',
            field=models.TextField(help_text='Name of the Fivetran service, uses keys from services.yaml as value', max_length=255, null=True),
        ),
    ]
