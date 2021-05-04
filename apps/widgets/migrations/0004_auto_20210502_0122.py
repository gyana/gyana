# Generated by Django 3.2 on 2021-05-02 01:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0003_widget_dataset'),
    ]

    operations = [
        migrations.AddField(
            model_name='widget',
            name='kind',
            field=models.CharField(choices=[('column2d', 'Column'), ('line', 'Line'), ('pie2d', 'Pie')], default='column2d', max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='widget',
            name='label',
            field=models.CharField(max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='value',
            field=models.CharField(max_length=300, null=True),
        ),
    ]
