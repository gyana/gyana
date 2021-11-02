from dataclasses import asdict, dataclass
from itertools import chain
from typing import Dict, List, Optional

from apps.base import clients
from apps.connectors.bigquery import check_bq_id_exists, get_bq_ids_from_dataset_safe

from ..models import Connector
from .config import get_services

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


class FivetranSchemaObj:
    def __init__(self, schemas_dict, connector):
        service_conf = get_services()[connector.service]

        self.connector = connector
        self.requires_schema_prefix = service_conf.get("requires_schema_prefix") == "t"
        self.schema_prefix = connector.schema if self.requires_schema_prefix else None
        self.schemas = [FivetranSchema(key=k, **s) for k, s in schemas_dict.items()]

    def to_dict(self):
        return {s.key: s.asdict() for s in self.schemas}

    def get_bq_datasets(self):

        service = get_services()[self.connector.service]

        # used in deletion to determine bigquery datasets associated with a connector

        if not service.get("service_type", "api_cloud") != "database":
            return {self.schema_prefix}

        # a database connector used multiple bigquery datasets
        return {
            f"{self.schema_prefix}_{s.name_in_destination}"
            for s in self.schemas
            if s.enabled
        }

    def get_bq_ids(self):

        # definitive function to map from a fivetran schema object to one or more
        # bigquery schemas with one or more tables
        #
        # api_cloud = fixed tables in one schema
        # database = fixed tables in multiple schemas
        # webhooks_reports = single table in one schema (no schema provided)
        # event_tracking = dynamic tables in one schema (no schema provided)
        #
        # the fivetran getting started diagram has a good summary of the options
        # https://fivetran.com/docs/getting-started/core-concepts
        # and the rest of the docs cover each section in detail
        #
        # an empty return indicates that there is no data in bigquery yet

        service = get_services()[self.connector.service]
        service_type = service.get("service_type", "api_cloud")

        # event_tracking
        if service_type == "event_tracking":
            return get_bq_ids_from_dataset_safe(self.schema_prefix)

        # webhooks_reports
        if service_type == "webhooks_reports":
            bq_id = f'{self.schema_prefix}.{service["static_config"]["table"]}'
            return {bq_id} if check_bq_id_exists(bq_id) else {}

        # api_cloud
        if service_type == "api_cloud":
            actual_bq_ids = get_bq_ids_from_dataset_safe(self.schema_prefix)
            schema_bq_ids = {
                f"{self.schema_prefix}.{table.name_in_destination}"
                for table in self.schemas[0].tables
                if table.is_enabled
            }
            return actual_bq_ids & schema_bq_ids

        # databases
        enabled_schemas = [s for s in self.schemas if s.enabled]
        actual_bq_ids = {
            get_bq_ids_from_dataset_safe(
                f"{self.schema_prefix}_{schema.name_in_destination}"
            )
            for schema in enabled_schemas
        }
        actual_bq_ids = set(chain(*actual_bq_ids))

        schema_bq_ids = {
            f"{self.schema_prefix}_{schema.name_in_destination}.{table.name_in_destination}"
            for schema in enabled_schemas
            for table in schema.tables
            if table.is_enabled
        }
        return actual_bq_ids & schema_bq_ids


# def schemas_to_obj(schemas_dict):
#     return [FivetranSchema(key=k, **s) for k, s in schemas_dict.items()]


# def schemas_to_dict(schemas):
#     return {s.key: s.asdict() for s in schemas}


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
