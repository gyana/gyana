from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import ibis

if TYPE_CHECKING:
    from apps.tables.models import Table
    from apps.uploads.models import Upload


class BaseClient(ABC):
    client: ibis.BaseBackend

    @abstractmethod
    def get_table(self, table: "Table"):
        raise NotImplementedError

    @abstractmethod
    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        raise NotImplementedError
