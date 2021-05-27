from django.core.exceptions import ImproperlyConfigured
from django.utils.html import escape
from django.utils.http import urlencode
from django_tables2 import Column, Table
from django_tables2.data import TableData
from django_tables2.templatetags.django_tables2 import QuerystringNode
from lib.clients import ibis_client

# Monkey path the querystring templatetag for the pagination links
# Without this links only lead to the whole document url and add query parameter
# instead we want to link to the turbo-frame/request url

context_processor_error_msg = (
    "Tag {%% %s %%} requires django.template.context_processors.request to be "
    "in the template configuration in "
    "settings.TEMPLATES[]OPTIONS.context_processors) in order for the included "
    "template tags to function correctly."
)


def render(self, context):
    if "request" not in context:
        raise ImproperlyConfigured(context_processor_error_msg % "querystring")

    params = dict(context["request"].GET)
    for key, value in self.updates.items():
        if isinstance(key, str):
            params[key] = value
            continue
        key = key.resolve(context)
        value = value.resolve(context)
        if key not in ("", None):
            params[key] = value
    for removal in self.removals:
        params.pop(removal.resolve(context), None)

    value = escape("?" + urlencode(params, doseq=True))

    if self.asvar:
        context[str(self.asvar)] = value
        return ""
    else:
        # This is the only change in this function
        # we are adding the whole path instead of only the query parameters
        return context["request"].path + value


QuerystringNode.render = render


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
        conn = ibis_client()
        df = conn.execute(self.data.limit(page.stop - page.start, offset=page.start))
        return df.to_dict(orient="records")

    # TODO: This request slows down the loading of data a lot.
    def __len__(self):
        """Fetches the total size from BigQuery"""
        conn = ibis_client()
        return conn.execute(self.data.count())

    # Not sure when or whether this is used at the moment
    def __iter__(self):
        for offset in range(
            0,
            len(self),
            self.rows_per_page,
        ):
            yield self[offset]
        return

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
    attrs = {name: Column() for name in schema}
    attrs["Meta"] = type("Meta", (), {"attrs": {"class": "table"}})
    table_class = type("DynamicTable", (Table,), attrs)

    table_data = BigQueryTableData(query)
    return table_class(data=table_data, **kwargs)
