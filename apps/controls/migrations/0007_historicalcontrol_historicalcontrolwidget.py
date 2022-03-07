# Generated by Django 3.2.11 on 2022-03-07 12:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import simple_history.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('dashboards', '0023_alter_dashboard_shared_id'),
        ('widgets', '0054_historicalcombinationchart'),
        ('controls', '0006_auto_20220114_1240'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalControlWidget',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, editable=False)),
                ('updated', models.DateTimeField(blank=True, editable=False)),
                ('x', models.IntegerField(default=0, help_text='The x field is in absolute pixel value.')),
                ('y', models.IntegerField(default=0, help_text='The y field is in absolute pixel value.')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('control', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='controls.control')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('page', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='dashboards.page')),
            ],
            options={
                'verbose_name': 'historical control widget',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalControl',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created', models.DateTimeField(blank=True, editable=False)),
                ('updated', models.DateTimeField(blank=True, editable=False)),
                ('kind', models.CharField(default='date_range', max_length=16)),
                ('start', models.DateTimeField(blank=True, help_text='Select the start date', null=True)),
                ('end', models.DateTimeField(blank=True, help_text='Select the end date', null=True)),
                ('date_range', models.CharField(blank=True, choices=[('today', 'today'), ('tomorrow', 'tomorrow'), ('yesterday', 'yesterday'), ('oneweekago', 'one week ago'), ('onemonthago', 'one month ago'), ('oneyearago', 'one year ago'), ('thisweek', 'This week (starts Monday)'), ('thisweekuptodate', 'This week (starts Monday) up to date'), ('lastweek', 'Last week (starts Monday)'), ('last7', 'Last 7 days'), ('last14', 'Last 14 days'), ('last28', 'Last 28 days'), ('thismonth', 'This month'), ('thismonthuptodate', 'This month to date'), ('lastmonth', 'Last month'), ('last30', 'Last 30 days'), ('last90', 'Last 90 days'), ('thisquarter', 'This quarter'), ('thisquarteruptodate', 'This quarter up to date'), ('lastquarter', 'Last quarter'), ('last180', 'Last 180 days'), ('last12month', 'Last 12 months'), ('lastfull12month', 'Last full 12 months until today'), ('lastyear', 'Last calendar year'), ('thisyear', 'This year'), ('thisyearuptodate', 'This year (January - up to date)'), ('custom', 'Custom')], default='thisyear', help_text='Select the time period', max_length=20)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('page', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='dashboards.page')),
                ('widget', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='widgets.widget')),
            ],
            options={
                'verbose_name': 'historical control',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
