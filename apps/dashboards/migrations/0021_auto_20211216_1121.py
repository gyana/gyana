# Generated by Django 3.2.7 on 2021-12-16 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0020_dashboard_font_family'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboard',
            name='show_widget_border',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='dashboard',
            name='font_family',
            field=models.CharField(choices=[('Boogaloo', 'Boogaloo'), ('Lato', 'Lato'), ('Merriweather', 'Merriweather'), ('Montserrat', 'Montserrat'), ('Open Sans', 'Open Sans'), ('Roboto', 'Roboto'), ('Ubuntu', 'Ubuntu')], default='Roboto', max_length=30),
        ),
    ]
