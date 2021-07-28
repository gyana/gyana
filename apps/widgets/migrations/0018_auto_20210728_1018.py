# Generated by Django 3.2.5 on 2021-07-28 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0017_alter_widget_width'),
    ]

    operations = [
        migrations.AddField(
            model_name='widget',
            name='sort_ascending',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='sort_by',
            field=models.CharField(choices=[('label', 'Label'), ('value', 'Value')], default='value', max_length=12),
        ),
    ]
