from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from apps.base import clients
from apps.connectors.bigquery import check_bq_id_exists, get_bq_ids_from_dataset_safe

from .config import ServiceTypeEnum

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
    service_type: ServiceTypeEnum
    schema_prefix: str

    name_in_destination: str
    enabled: bool
    tables: List[FivetranTable]

    def __post_init__(self):
        self.tables = [FivetranTable(key=k, **t) for k, t in self.tables.items()]

    def asdict(self):
        res = {**asdict(self), "tables": {t.key: t.asdict() for t in self.tables}}
        res.pop("key")
        res.pop("service_type")
        res.pop("schema_prefix")
        return res

    @property
    def dataset_id(self):
        if self.service_type == ServiceTypeEnum.DATABASE:
            return f"{self.schema_prefix}_{self.name_in_destination}"
        return self.schema_prefix

    @property
    def enabled_bq_ids(self):
        return {
            f"{self.dataset_id}.{table.name_in_destination}"
            for table in self.tables
            if table.enabled
        }

    @property
    def display_name(self):
        return self.name_in_destination.replace("_", " ").title()


class FivetranSchemaObj:
    def __init__(self, schemas_dict, connector):
        self.conf = connector.conf
        self.schema_prefix = connector.schema
        self.schemas = [
            FivetranSchema(
                key=k,
                service_type=self.conf.service_type,
                schema_prefix=self.schema_prefix,
                **s,
            )
            for k, s in schemas_dict.items()
        ]

    def to_dict(self):
        return {s.key: s.asdict() for s in self.schemas}

    def get_bq_datasets(self):

        # used in deletion to determine bigquery datasets associated with a connector

        if not self.conf.service_type != ServiceTypeEnum.DATABASE:
            return {self.schema_prefix}

        # a database connector used multiple bigquery datasets
        return {s.dataset_id for s in self.schemas if s.enabled}

    def get_bq_ids(self):

        # definitive function to map from a fivetran schema object to one or more
        # bigquery schemas with one or more tables
        #
        # an empty return indicates that there is no data in bigquery yet

        service_type = self.conf.service_type

        # event_tracking
        if service_type == ServiceTypeEnum.EVENT_TRACKING:
            return get_bq_ids_from_dataset_safe(self.schema_prefix)

        # webhooks_reports
        if service_type == ServiceTypeEnum.WEBHOOKS_REPORTS:
            bq_id = f'{self.schema_prefix}.{self.conf.static_config["table"]}'
            return {bq_id} if check_bq_id_exists(bq_id) else {}

        # api_cloud
        if service_type == ServiceTypeEnum.API_CLOUD:
            actual_bq_ids = get_bq_ids_from_dataset_safe(self.schema_prefix)
            # only databases have multiple schemas
            schema_bq_ids = self.schemas[0].enabled_bq_ids
            return actual_bq_ids & schema_bq_ids

        # databases
        actual_bq_ids = {
            bq_id
            for dataset_id in self.get_bq_datasets()
            for bq_id in get_bq_ids_from_dataset_safe(dataset_id)
        }
        schema_bq_ids = {
            bq_id for s in self.schemas for bq_id in s.enabled_bq_ids if s.enabled
        }
        return actual_bq_ids & schema_bq_ids


def update_schema_from_cleaned_data(connector, cleaned_data):
    # construct the payload from cleaned data

    # mutate the schema information based on user input
    schema_obj = clients.fivetran().get_schemas(connector)

    for schema in schema_obj.schemas:
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

    clients.fivetran().update_schemas(connector, schema_obj)
