from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import ibis

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
