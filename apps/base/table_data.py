import pandas as pd
from apps.base.clients import bigquery_client, get_dataframe
from django_tables2 import Column, Table
from django_tables2.data import TableData
from django_tables2.templatetags.django_tables2 import QuerystringNode

# Monkey patch the querystring templatetag for the pagination links
# Without this links only lead to the whole document url and add query parameter
# instead we want to link to the turbo-frame/request url


old_render = QuerystringNode.render


def new_render(self, context):
    value = old_render(self, context)
    # we are adding the whole path instead of only the query parameters
    return context["request"].path + value


QuerystringNode.render = new_render


def _replace_nulls_with_none(df: pd.DataFrame):
    # pandas to_dict returns non python native types e.g. Timestamp, NaT and nan
    # short term fix to remove bugs with sentinel null values
    # https://github.com/pandas-dev/pandas/issues/16248
    # longer term fix would add custom renderer to columns in DynamicTable
    return df.astype(object).where(df.notnull(), None)


class BigQueryTableData(TableData):
    """Django table data class that queries data from BigQuery

    See https://github.com/jieter/django-tables2/blob/master/django_tables2/data.py
    """

    rows_per_page = 100

    def __init__(
        self,
        data,
    ):
        self.data = data

    def __getitem__(self, page: slice):
        """Fetches the data for the current page"""
        df = get_dataframe(
            self.data.limit(page.stop - page.start, offset=page.start).compile()
        )
        df = _replace_nulls_with_none(df)
        return df.to_dict(orient="records")

    def __len__(self):
        """Fetches the total size from BigQuery"""
        return self.data.bq_table.num_rows

    # Not sure when or whether this is used at the moment
    def __iter__(self):
        for offset in range(
            0,
            len(self),
            self.rows_per_page,
        ):
            yield self[offset]
        return

    def order_by(self, aliases):
        self.data = self.data.sort_by(
            [(alias.replace("-", ""), alias.startswith("-")) for alias in aliases]
        )

    def set_table(self, table):
        """
        `Table.__init__` calls this method to inject an instance of itself into the
        `TableData` instance.
        Good place to do additional checks if Table and TableData instance will work
        together properly.
        """
        self.table = table


def get_table(schema, query, **kwargs):
    """Dynamically creates a table class and adds the correct table data

    See https://django-tables2.readthedocs.io/en/stable/_modules/django_tables2/views.html
    """
    # Inspired by https://stackoverflow.com/questions/16696066/django-tables2-dynamically-adding-columns-to-table-not-adding-attrs-to-table
    attrs = {name: Column(verbose_name=name) for name in schema}
    attrs["Meta"] = type("Meta", (), {"attrs": {"class": "table"}})
    table_class = type("DynamicTable", (Table,), attrs)

    table_data = BigQueryTableData(query)
    return table_class(data=table_data, **kwargs)
