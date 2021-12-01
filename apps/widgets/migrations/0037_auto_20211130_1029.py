# Generated by Django 3.2.7 on 2021-11-30 10:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0036_alter_widget_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='widget',
            name='kind',
            field=models.CharField(choices=[('text', 'Text'), ('metric', 'Metric'), ('table', 'Table'), ('mscolumn2d', 'Column'), ('stackedcolumn2d', 'Stacked Column'), ('msbar2d', 'Bar'), ('stackedbar2d', 'Stacked Bar'), ('msline', 'Line'), ('msline-stacked', 'Stacked Line'), ('pie2d', 'Pie'), ('msarea', 'Area'), ('doughnut2d', 'Donut'), ('scatter', 'Scatter'), ('funnel', 'Funnel'), ('pyramid', 'Pyramid'), ('radar', 'Radar'), ('bubble', 'Bubble'), ('heatmap', 'Heatmap'), ('timeseries-line', 'Line Timeseries'), ('timeseries-line_stacked', 'Stacked Line Timeseries'), ('timeseries-column', 'Column Timeseries'), ('timeseries-column-stacked', 'Stacked Column Timeseries'), ('timeseries-area', 'Area Timeseries'), ('mscombidy2d', 'Combination chart')], default='mscolumn2d', max_length=32),
        ),
        migrations.CreateModel(
            name='CombinationChart',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('kind', models.CharField(choices=[('line', 'Line'), ('area', 'Area'), ('column', 'Column')], default='column', max_length=32)),
                ('column', models.CharField(max_length=300)),
                ('function', models.CharField(choices=[('sum', 'Sum'), ('count', 'Count'), ('nunique', 'Count distinct'), ('mean', 'Average'), ('max', 'Maximum'), ('min', 'Minimum'), ('std', 'Standard deviation')], max_length=20)),
                ('on_secondary', models.BooleanField(default=False, help_text='Plot on a secondary Y axis')),
                ('widget', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='charts', to='widgets.widget')),
            ],
            options={
                'ordering': ('-updated',),
                'abstract': False,
            },
        ),
    ]
