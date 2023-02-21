import functools
import math
from decimal import Decimal
from numbers import Number

import ibis.expr.datatypes as dt
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.template.loader import get_template
from django_tables2 import Column, Table
from django_tables2.config import RequestConfig as BaseRequestConfig
from django_tables2.data import TableData

from apps.base import clients
from apps.base.core.utils import md5
from apps.columns.currency_symbols import CURRENCY_SYMBOLS_MAP


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
        self._len_key = f"cache-table-length-{hash(self.data)}"

    @property
    def _page_selected(self):
        return "page" in self.table.request.GET

    @functools.cache
    def _get_query_results(self, start=0, stop=None):
        data = self.data
        if start > 0:
            data = data.limit(stop - start, offset=start)
        return clients.bigquery().get_query_results(
            data.compile(), max_results=self.rows_per_page
        )

    def __getitem__(self, page: slice):
        """Fetches the data for the current page"""
        return (
            self._get_query_results(page.start, page.stop).rows_dict_by_md5
            if self._page_selected
            else self._get_query_results().rows_dict_by_md5[: page.stop - page.start]
        )

    def __len__(self):
        """Fetches the total size from BigQuery"""
        total_rows = cache.get(self._len_key)

        if not self._page_selected or total_rows is None:
            total_rows = self._get_query_results().total_rows
            cache.set(self._len_key, total_rows, 24 * 3600)

        return total_rows

    def get_column_from_md5(self, md5):
        return self.table.columns[md5].verbose_name

    def order_by(self, aliases):
        sort_by = [
            (self.get_column_from_md5(alias.replace("-", "")), alias.startswith("-"))
            for alias in aliases
        ]
        # If data has a ordering set we need to overwrite it
        if hasattr(self.data.op(), "sort_keys"):
            self.data = self.data.projection([]).sort_by(sort_by)
        else:
            self.data = self.data.sort_by(sort_by)

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


def get_type_name(type_):
    if isinstance(type_, (dt.Floating, dt.Integer, dt.Decimal)):
        return "Numeric"
    if isinstance(type_, dt.String):
        return "String"
    if isinstance(type_, dt.Boolean):
        return "Boolean"
    if isinstance(type_, (dt.Time)):
        return "Time"
    if isinstance(type_, dt.Date):
        return "Date"
    if isinstance(type_, dt.Timestamp):
        return "Date & Time"
    if isinstance(type_, dt.Struct):
        return "Dictionary"


def get_type_class(type_):
    if isinstance(type_, (dt.Floating, dt.Integer, dt.Decimal)):
        return "column column--numeric"
    if isinstance(type_, dt.String):
        return "column column--string"
    if isinstance(type_, dt.Boolean):
        return "column column--boolean"
    if isinstance(type_, dt.Time):
        return "column column--time"
    if isinstance(type_, dt.Date):
        return "column column--date"
    if isinstance(type_, dt.Timestamp):
        return "column column--datetime"
    if isinstance(type_, dt.Struct):
        return "column column--dict"


validateURL = URLValidator()


class BigQueryColumn(Column):
    def __init__(self, **kwargs):
        settings = kwargs.pop("settings") or {}
        self.summary = kwargs.pop("footer") or None

        # If hasattr(self, 'render_footer') returns True django-tables2 always
        # renders the footer, even if there are no values.
        if self.summary:
            self.render_footer = self._render_footer

        super().__init__(**kwargs)

        self.verbose_name = settings.get("name") or self.verbose_name
        self.rounding = settings.get("rounding", 2)
        self.currency = settings.get("currency")
        self.is_percentage = settings.get("is_percentage")
        self.conditional_formatting = settings.get("conditional_formatting")
        self.positive_threshold = settings.get("positive_threshold")
        self.negative_threshold = settings.get("negative_threshold")

    def render(self, value):
        if isinstance(value, (float, Decimal)) and math.isinf(value):
            value = "∞"

        # TODO: Add a tooltip to explain this or find a better label.
        if isinstance(value, (float, Decimal)) and math.isnan(value):
            value = "NaN"

        if value is None:
            return get_template("columns/empty_cell.html").render()

        if isinstance(value, Number) and self.conditional_formatting:
            self.attrs["td"] = {
                **self.attrs.get("td", {}),
                "class": "bg-green-50"
                if value > self.positive_threshold
                else "bg-red-50"
                if value < self.negative_threshold
                else None,
            }
        if isinstance(value, Number) and self.currency:
            return get_template("columns/currency_cell.html").render(
                {
                    "value": value,
                    "currency": CURRENCY_SYMBOLS_MAP[self.currency],
                    "rounding": self.rounding,
                }
            )
        if isinstance(value, (float, Decimal)):
            value = value * 100 if self.is_percentage else value

            return get_template("columns/float_cell.html").render(
                {
                    "value": value,
                    "clean_value": int(value)
                    if self.rounding == 0
                    else round(value, self.rounding),
                    "is_percentage": self.is_percentage,
                }
            )
        if isinstance(value, bool) or value == "True" or value == "False":
            return get_template("columns/bool_cell.html").render({"value": value})
        if isinstance(value, int):
            return get_template("columns/int_cell.html").render(
                {"value": value, "is_percentage": self.is_percentage}
            )
        # First checking if a string is a link to hyperlink it.
        if isinstance(value, str):
            try:
                validateURL(value)  # Will error if not a link.
                return get_template("columns/link_cell.html").render({"value": value})
            except ValidationError:
                pass
        if isinstance(value, str) and len(value) >= 64:
            # Truncate row values above 61 characters (61 + 3 ellipsis = 64).
            return get_template("columns/string_cell.html").render(
                {"value": f"{value[:61]}...", "tooltip": value}
            )

        return super().render(value)

    def _render_footer(self, bound_column, table):
        return self.render(self.summary)


def get_table(schema, query, footer=None, settings=None, **kwargs):
    """Dynamically creates a table class and adds the correct table data

    See https://django-tables2.readthedocs.io/en/stable/_modules/django_tables2/views.html
    """
    attrs = {}
    settings = settings or {}
    url = kwargs.pop("url", None)

    # Inspired by https://stackoverflow.com/questions/16696066/django-tables2-dynamically-adding-columns-to-table-not-adding-attrs-to-table
    for name, type_ in schema.items():
        attrs[md5(name)] = BigQueryColumn(
            empty_values=(),
            settings=settings.get(name),
            verbose_name=name,
            attrs={
                "th": {
                    "class": get_type_class(type_),
                    "x-tooltip": get_type_name(type_),
                },
                **(
                    {
                        "td": {"style": "text-align: right;"},
                        "tf": {"style": "text-align: right;"},
                    }
                    if isinstance(type_, (dt.Floating, dt.Integer))
                    else {}
                ),
            }
            if not settings.get("hide_data_type")
            else {},
            footer=footer.get(name) if footer else None,
        )

    attrs["Meta"] = type(
        "Meta",
        (),
        {
            "attrs": {"class": "table", **({"url": url} if url else {})},
        },
    )
    table_class = type("DynamicTable", (Table,), attrs)

    table_data = BigQueryTableData(query)
    return table_class(data=table_data, **kwargs)
