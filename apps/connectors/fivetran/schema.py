from dataclasses import asdict, dataclass
from itertools import chain
from typing import Dict, List, Optional

from apps.base import clients

from ..models import Connector

# wrapper for fivetran schema information
# https://fivetran.com/docs/rest-api/connectors#retrieveaconnectorschemaconfig
# the schema includes the datasets, tables and individual columns
# we can modify the schema to only sync certain tables into the data warehouse


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

    @property
    def display_name(self):
        return self.name_in_destination.replace("_", " ").title()


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

    @property
    def display_name(self):
        return self.name_in_destination.replace("_", " ").title()


def schemas_to_obj(schemas_dict):
    return [FivetranSchema(key=k, **s) for k, s in schemas_dict.items()]


def schemas_to_dict(schemas):
    return {s.key: s.asdict() for s in schemas}


def get_bq_datasets_from_schemas(connector):

    datasets = {
        s.name_in_destination for s in clients.fivetran().get_schemas(connector)
    }

    # fivetran schema config does not include schema prefix for databases
    if connector.is_database:
        datasets = {f"{connector.schema}_{id_}" for id_ in datasets}

    return datasets


def get_bq_ids_from_schemas(connector: Connector):

    # get the list of bigquery ids (dataset.table) from the fivetran schema information

    schema_bq_ids = set(
        chain(*(s.enabled_bq_ids for s in clients.fivetran().get_schemas(connector)))
    )

    # fivetran schema config does not include schema prefix for databases
    if connector.is_database:
        schema_bq_ids = {f"{connector.schema}_{id_}" for id_ in schema_bq_ids}

    # special case for google sheets
    if len(schema_bq_ids) == 0:
        return [f"{connector.schema}.sheets_table"]

    return schema_bq_ids


def update_schema_from_cleaned_data(connector, cleaned_data):
    # construct the payload from cleaned data

    # mutate the schema information based on user input
    schemas = clients.fivetran().get_schemas(connector)

    for schema in schemas:
        schema.enabled = f"{schema.name_in_destination}_schema" in cleaned_data
        # only patch tables that are allowed
        schema.tables = [
            t for t in schema.tables if t.enabled_patch_settings["allowed"]
        ]
        for table in schema.tables:
            # field does not exist if all unchecked
            table.enabled = table.name_in_destination in cleaned_data.get(
                f"{schema.name_in_destination}_tables", []
            )
            # no need to patch the columns information and it can break
            # if access issues, e.g. per column access in Postgres
            table.columns = {}

    clients.fivetran().update_schemas(connector, schemas)
