# Generated by Django 3.2 on 2021-07-12 09:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0006_auto_20210625_0951'),
        ('workflows', '0036_alter_node_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='column',
            name='column',
            field=models.CharField(help_text='Select columns', max_length=300),
        ),
        migrations.AlterField(
            model_name='node',
            name='input_table',
            field=models.ForeignKey(help_text='Select a data source', null=True, on_delete=django.db.models.deletion.CASCADE, to='tables.table'),
        ),
        migrations.AlterField(
            model_name='node',
            name='join_how',
            field=models.CharField(choices=[('inner', 'Inner'), ('outer', 'Outer'), ('left', 'Left'), ('right', 'Right')], default='inner', help_text='Select the join method, more information in the docs', max_length=12),
        ),
        migrations.AlterField(
            model_name='node',
            name='join_left',
            field=models.CharField(blank=True, help_text='The column from the first parent you want to join on.', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='join_right',
            field=models.CharField(blank=True, help_text='The column from the second parent you want to join on.', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='limit_limit',
            field=models.IntegerField(default=100, help_text='Limits rows to selected number'),
        ),
        migrations.AlterField(
            model_name='node',
            name='limit_offset',
            field=models.IntegerField(help_text='From where to start the limit', null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='output_name',
            field=models.CharField(help_text='Name your output, this name will be refered to in other workflows or dashboards.', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='pivot_aggregation',
            field=models.CharField(blank=True, choices=[('sum', 'Sum'), ('count', 'Count'), ('mean', 'Average'), ('max', 'Maximum'), ('min', 'Minimum'), ('std', 'Standard deviation')], help_text='Select an aggregation to be applied to the new cells', max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='pivot_column',
            field=models.CharField(blank=True, help_text='The column whose values create the new column names', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='pivot_index',
            field=models.CharField(blank=True, help_text='Which column to keep as index', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='pivot_value',
            field=models.CharField(blank=True, help_text='The column containing the values for the new pivot cells', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='select_mode',
            field=models.CharField(choices=[('keep', 'keep'), ('exclude', 'exclude')], default='keep', help_text='Either keep or exclude the selected columns', max_length=8),
        ),
        migrations.AlterField(
            model_name='node',
            name='union_distinct',
            field=models.BooleanField(default=False, help_text='Ignore common rows if selected'),
        ),
        migrations.AlterField(
            model_name='node',
            name='union_mode',
            field=models.CharField(choices=[('keep', 'keep'), ('exclude', 'exclude')], default='except', help_text='Either keep or exclude the common rows', max_length=8),
        ),
        migrations.AlterField(
            model_name='node',
            name='unpivot_column',
            field=models.CharField(blank=True, help_text='Name of the new category column', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='node',
            name='unpivot_value',
            field=models.CharField(blank=True, help_text='Name of the new value column', max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='sortcolumn',
            name='ascending',
            field=models.BooleanField(default=True, help_text='Select to sort ascendingly'),
        ),
        migrations.AlterField(
            model_name='sortcolumn',
            name='column',
            field=models.CharField(help_text='Select column to sort on', max_length=300),
        ),
    ]
