from functools import cached_property

from django_tables2.data import TableData
from lib.clients import ibis_client


class BigQueryTableData(TableData):
    rows_per_page = 100

    def __init__(
        self,
        data,
    ):
        self.data = data

    def __getitem__(self, page):
        conn = ibis_client()
        df = conn.execute(self.data.limit(page.stop - page.start, offset=page.start))
        return df.to_dict(orient="records")

    def __len__(self):
        conn = ibis_client()
        return conn.execute(self.data.count())

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
