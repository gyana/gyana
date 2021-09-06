from functools import cached_property

from apps.base.clients import get_query_results
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
        # todo: cache the row count after initial query
        # query_results = get_query_results(
        #     self.data.limit(page.stop - page.start, offset=page.start).compile()
        # )
        return [{k: v for k, v in row.items()} for row in self._query_results.rows]

    def __len__(self):
        """Fetches the total size from BigQuery"""
        return self._query_results.total_rows

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

    @cached_property
    def _query_results(self):
        return get_query_results(self.data.compile())


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
