# Generated by Django 3.2.11 on 2022-01-14 12:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboards', '0022_auto_20220105_1539'),
        ('widgets', '0045_widget_sort_column'),
        ('controls', '0005_alter_control_date_range'),
    ]

    operations = [
        migrations.AddField(
            model_name='control',
            name='widget',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='widgets.widget'),
        ),
        migrations.AlterField(
            model_name='control',
            name='date_range',
            field=models.CharField(blank=True, choices=[('today', 'today'), ('tomorrow', 'tomorrow'), ('yesterday', 'yesterday'), ('oneweekago', 'one week ago'), ('onemonthago', 'one month ago'), ('oneyearago', 'one year ago'), ('thisweek', 'This week (starts Monday)'), ('thisweekuptodate', 'This week (starts Monday) up to date'), ('lastweek', 'Last week (starts Monday)'), ('last7', 'Last 7 days'), ('last14', 'Last 14 days'), ('last28', 'Last 28 days'), ('thismonth', 'This month'), ('thismonthuptodate', 'This month to date'), ('lastmonth', 'Last month'), ('last30', 'Last 30 days'), ('last90', 'Last 90 days'), ('thisquarter', 'This quarter'), ('thisquarteruptodate', 'This quarter up to date'), ('lastquarter', 'Last quarter'), ('last180', 'Last 180 days'), ('last12month', 'Last 12 months'), ('lastfull12month', 'Last full 12 months until today'), ('lastyear', 'Last calendar year'), ('thisyear', 'This year'), ('thisyearuptodate', 'This year (January - up to date)'), ('custom', 'Custom')], default='thisyear', help_text='Select the time period', max_length=20),
        ),
        migrations.AlterField(
            model_name='control',
            name='end',
            field=models.DateTimeField(blank=True, help_text='Select the end date', null=True),
        ),
        migrations.AlterField(
            model_name='control',
            name='page',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboards.page'),
        ),
        migrations.AlterField(
            model_name='control',
            name='start',
            field=models.DateTimeField(blank=True, help_text='Select the start date', null=True),
        ),
    ]
