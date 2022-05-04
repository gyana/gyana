# Generated by Django 3.2.12 on 2022-05-04 09:28

from django.db import migrations, models


def forward(apps, schema_editor):
    Widget = apps.get_model("widgets", "Widget")
    AggregationColumn = apps.get_model("columns", "AggregationColumn")
    Column = apps.get_model("columns", "Column")
    for widget in Widget.objects.all():
        aggregations = widget.aggregations.order_by("created").all()
        for idx, aggregation in enumerate(aggregations):
            aggregation.sort_index = len(aggregations) - idx

        AggregationColumn.objects.bulk_update(aggregations, ["sort_index"])

        columns = widget.columns.order_by("created").all()
        for idx, column in enumerate(columns):
            column.sort_index = len(columns) - idx

        Column.objects.bulk_update(columns, ["sort_index"])


class Migration(migrations.Migration):

    dependencies = [
        ("columns", "0022_auto_20220503_1302"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="aggregationcolumn",
            options={"ordering": ("-sort_index",)},
        ),
        migrations.AlterModelOptions(
            name="column",
            options={"ordering": ("-sort_index",)},
        ),
        migrations.AddField(
            model_name="aggregationcolumn",
            name="sort_index",
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="column",
            name="sort_index",
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="historicalaggregationcolumn",
            name="sort_index",
            field=models.BigIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="historicalcolumn",
            name="sort_index",
            field=models.BigIntegerField(default=0),
        ),
        migrations.RunPython(forward, reverse_code=migrations.RunPython.noop),
    ]
