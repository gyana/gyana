from dataclasses import asdict, dataclass
from itertools import chain
from typing import Dict, List, Optional

from .config import ServiceTypeEnum
from .services.facebook_ads import get_enabled_table_ids_for_facebook_ads

SERVICE_TO_TABLE_IDS = {"facebook_ads": get_enabled_table_ids_for_facebook_ads}

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
    service: str
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
        res.pop("service")
        res.pop("service_type")
        res.pop("schema_prefix")
        return res

    @property
    def display_name(self):
        return self.name_in_destination.replace("_", " ").title()

    @property
    def dataset_id(self):
        # database connectors have multiple bigquery datasets
        if self.service_type == ServiceTypeEnum.DATABASE:
            return f"{self.schema_prefix}_{self.name_in_destination}"
        return self.schema_prefix

    @property
    def enabled_tables(self):
        return [table for table in self.tables if table.enabled]

    @property
    def enabled_table_ids(self):
        if self.service in SERVICE_TO_TABLE_IDS:
            return SERVICE_TO_TABLE_IDS[self.service](self.enabled_tables)
        return {table.name_in_destination for table in self.enabled_tables}

    @property
    def enabled_bq_ids(self):
        # the bigquery ids that fivetran intends to create based on the schema
        # the user can has the option to disable individual tables
        return {
            f"{self.dataset_id}.{table.name_in_destination}"
            for table in self.enabled_tables
        }


class FivetranSchemaObj:
    def __init__(self, schemas_dict, service, service_type, schema_prefix):
        self.schemas = (
            [
                FivetranSchema(
                    key=key,
                    service=service,
                    service_type=service_type,
                    schema_prefix=schema_prefix,
                    **schema,
                )
                for key, schema in schemas_dict.items()
            ]
            if schemas_dict
            else []
        )

    def to_dict(self):
        return {schema.key: schema.asdict() for schema in self.schemas}

    @property
    def enabled_schemas(self):
        # the user can has the option to disable individual schemas
        return [schema for schema in self.schemas if schema.enabled]

    @property
    def all_datasets(self):
        # all possible datasets, including those not enabled
        return {schema.dataset_id for schema in self.schemas}

    @property
    def enabled_bq_ids(self):
        # api_cloud only has one schema
        return set(chain(*(schema.enabled_bq_ids for schema in self.enabled_schemas)))

    def mutate_from_cleaned_data(self, cleaned_data, allowlist=None):
        # mutate the schema_obj based on cleaned_data from form

        for schema in self.schemas:
            schema.enabled = f"{schema.name_in_destination}_schema" in cleaned_data
            # only patch tables that are allowed
            schema.tables = [
                t for t in schema.tables if t.enabled_patch_settings["allowed"]
            ]
            for table in schema.tables:
                tables_allowlist = allowlist or cleaned_data.get(
                    f"{schema.name_in_destination}_tables", []
                )
                # field does not exist if all unchecked
                table.enabled = table.name_in_destination in tables_allowlist
                # no need to patch the columns information and it can break
                # if access issues, e.g. per column access in Postgres
                table.columns = {}
