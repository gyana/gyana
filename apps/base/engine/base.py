from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import ibis
from django.utils import timezone

if TYPE_CHECKING:
    from apps.customapis.models import CustomApi
    from apps.tables.models import Table
    from apps.teams.models import Team
    from apps.uploads.models import Upload


class BaseClient(ABC):
    client: ibis.BaseBackend

    @abstractmethod
    def get_table(self, table: "Table"):
        raise NotImplementedError

    @abstractmethod
    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        raise NotImplementedError

    @abstractmethod
    def create_team_dataset(self, team: "Team"):
        raise NotImplementedError

    @abstractmethod
    def delete_team_dataset(self, team: "Team"):
        raise NotImplementedError

    @abstractmethod
    def import_table_from_customapi(self, table: "Table", customapi: "CustomApi"):
        raise NotImplementedError

    def create_or_replace_table(self, table_id: str, query: str):
        # TODO: Update to ibis 7 to support create_tablr with overwrite=True
        self.client.raw_sql(f"CREATE OR REPLACE TABLE {table_id} as ({query})")

    def drop_table(self, table_id: str):
        self.client.drop_table(table_id, force=True)

    def get_modified_and_num_rows(self, table: "Table"):
        modified = timezone.now()
        num_rows = self.get_table(table).count().execute()
        return modified, num_rows
