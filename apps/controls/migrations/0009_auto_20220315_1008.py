# Generated by Django 3.2.12 on 2022-03-15 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('controls', '0008_auto_20220314_1158'),
    ]

    operations = [
        migrations.AddField(
            model_name='controlwidget',
            name='height',
            field=models.IntegerField(default=60, help_text='The height is in absolute pixel value.'),
        ),
        migrations.AddField(
            model_name='controlwidget',
            name='width',
            field=models.IntegerField(default=270, help_text='The width is in absolute pixel value.'),
        ),
        migrations.AddField(
            model_name='historicalcontrolwidget',
            name='height',
            field=models.IntegerField(default=60, help_text='The height is in absolute pixel value.'),
        ),
        migrations.AddField(
            model_name='historicalcontrolwidget',
            name='width',
            field=models.IntegerField(default=270, help_text='The width is in absolute pixel value.'),
        ),
    ]
