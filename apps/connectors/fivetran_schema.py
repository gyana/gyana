from dataclasses import asdict, dataclass
from itertools import chain
from typing import Dict, List, Optional

from apps.connectors.models import Connector

# wrapper for the Fivetran connectors REST API, documented here
# https://fivetran.com/docs/rest-api/connectors
# on error, raise a FivetranClientError and it will be managed in
# the caller (e.g. form) or trigger 500 (user can refresh/retry)


@dataclass
class FivetranTable:
    key: str
    name_in_destination: str
    enabled: bool
    enabled_patch_settings: Dict
    columns: Optional[List[Dict]] = None

    def asdict(self):
        res = asdict(self)
        res.pop("key")
        if self.columns is None:
            res.pop("columns")
        return res


@dataclass
class FivetranSchema:
    key: str
    name_in_destination: str
    enabled: bool
    tables: List[FivetranTable]

    def __post_init__(self):
        self.tables = [FivetranTable(key=k, **t) for k, t in self.tables.items()]

    def asdict(self):
        res = {**asdict(self), "tables": {t.key: t.asdict() for t in self.tables}}
        res.pop("key")
        return res

    @property
    def enabled_bq_ids(self):
        return {
            f"{self.name_in_destination}.{table.name_in_destination}"
            for table in self.tables
            if table.enabled and self.enabled
        }


def schemas_to_obj(schemas_dict):
    return [FivetranSchema(key=k, **s) for k, s in schemas_dict.items()]


def schemas_to_dict(schemas):
    return {s.key: s.asdict() for s in schemas}


def get_bq_datasets_from_schemas(connector):

    from apps.base.clients import fivetran_client

    datasets = {s.name_in_destination for s in fivetran_client().get_schemas(connector)}

    # fivetran schema config does not include schema prefix for databases
    if connector.is_database:
        datasets = {f"{connector.schema}_{id_}" for id_ in datasets}

    return datasets


def get_bq_ids_from_schemas(connector: Connector):

    # get the list of bigquery ids (dataset.table) from the fivetran schema information

    from apps.base.clients import fivetran_client

    schema_bq_ids = set(
        chain(*(s.enabled_bq_ids for s in fivetran_client().get_schemas(connector)))
    )

    # fivetran schema config does not include schema prefix for databases
    if connector.is_database:
        schema_bq_ids = {f"{connector.schema}_{id_}" for id_ in schema_bq_ids}

    if len(schema_bq_ids) == 0:
        return [f"{connector.schema}.sheets_table"]

    return schema_bq_ids
