# Generated by Django 3.2.11 on 2022-02-23 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0050_remove_widget_rounding_decimal'),
    ]

    operations = [
        migrations.AddField(
            model_name='widget',
            name='metric_comparison_font_color',
            field=models.CharField(max_length=7, null=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='metric_comparison_font_size',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='metric_font_color',
            field=models.CharField(max_length=7, null=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='metric_font_size',
            field=models.IntegerField(null=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='metric_header_font_color',
            field=models.CharField(max_length=7, null=True),
        ),
        migrations.AddField(
            model_name='widget',
            name='metric_header_font_size',
            field=models.IntegerField(null=True),
        ),
    ]
