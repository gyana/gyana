import functools

from django.core.cache import cache
from django_tables2 import Column, Table
from django_tables2.config import RequestConfig as BaseRequestConfig
from django_tables2.data import TableData
from django_tables2.templatetags.django_tables2 import QuerystringNode

from apps.base.clients import bigquery_client

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

    If pagination is not supplied, the client queries the entire result and
    fetches the first N rows, and the total rows information. The total rows
    information is cached, for future requests with explicit pages, where the
    data is fetched via LIMIT ... OFFSET ... expression.
    """

    rows_per_page = 50

    def __init__(
        self,
        data,
    ):
        self.data = data
        # calculate before the order_by is applied, as len is not effected
        self._len_key = str(hash(self.data))

    @property
    def _page_selected(self):
        return "page" in self.table.request.GET

    @functools.cache
    def _get_query_results(self, start=0, stop=None):
        data = self.data
        if start > 0:
            data = data.limit(stop - start, offset=start)
        return bigquery_client().get_query_results(
            data.compile(), max_results=self.rows_per_page
        )

    def __getitem__(self, page: slice):
        """Fetches the data for the current page"""
        if not self._page_selected:
            return self._get_query_results().rows_dict[: page.stop - page.start]
        return self._get_query_results(page.start, page.stop).rows_dict

    def __len__(self):
        """Fetches the total size from BigQuery"""
        total_rows = cache.get(self._len_key)

        if not self._page_selected or total_rows is None:
            total_rows = self._get_query_results().total_rows
            cache.set(self._len_key, total_rows, 24 * 3600)

        return total_rows

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


class RequestConfig(BaseRequestConfig):
    def configure(self, table):
        # table has request attribute before table_data.__len__ is called
        table.request = self.request
        return super().configure(table)


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
