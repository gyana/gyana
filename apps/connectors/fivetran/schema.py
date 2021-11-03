from dataclasses import asdict, dataclass
from itertools import chain
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
        # database connectors have multiple bigquery datasets
        if self.service_type == ServiceTypeEnum.DATABASE:
            return f"{self.schema_prefix}_{self.name_in_destination}"
        return self.schema_prefix

    @property
    def enabled_bq_ids(self):
        # the bigquery ids that fivetran intends to create based on the schema
        # the user can has the option to disable individual tables
        return {
            f"{self.dataset_id}.{table.name_in_destination}"
            for table in self.tables
            if table.enabled
        }

    @property
    def actual_bq_ids(self):
        # the actual bigquery ids we see in bigquery
        return get_bq_ids_from_dataset_safe(self.dataset_id)

    def get_bq_ids(self):
        # determine the bigquery ids we want to map into our database for this
        # schema. we take the intersection of what fivetran says it will create
        # vs what bigquery reports was actually created, this:
        #
        # - filters out tables that are incorrectly included in bigquery - e.g.
        #   failed deletions or fivetran system tables
        # - filters out tables that fivetran expected, but weren't created in
        #   bigquery - e.g. if the source app does not contain any of that entity
        #
        # nb: api_cloud and database only - webhooks_reports and event_tracking
        # do not have any fivetran schema information

        return self.actual_bq_ids & self.enabled_bq_ids

    @property
    def display_name(self):
        return self.name_in_destination.replace("_", " ").title()


class FivetranSchemaObj:
    def __init__(self, schemas_dict, service_conf, schema_prefix):
        self.conf = service_conf
        self.schema_prefix = schema_prefix
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

    @property
    def enabled_schemas(self):
        # the user can has the option to disable individual schemas
        return [s for s in self.schemas if s.enabled]

    def get_bq_datasets(self):

        # determine all the bigquery datasets associated with a connector,
        # used for deletions

        # a database connector used multiple bigquery datasets
        if self.conf.service_type == ServiceTypeEnum.DATABASE:
            return {s.dataset_id for s in self.enabled_schemas}

        return {self.schema_prefix}

    @property
    def enabled_bq_ids(self):

        # only defined for api_cloud and database

        service_type = self.conf.service_type

        # api_cloud
        # cross reference fivetran schema and bigquery dataset
        if service_type == ServiceTypeEnum.API_CLOUD:
            # only databases have multiple schemas
            return self.schemas[0].enabled_bq_ids

        # database
        # ditto api_cloud but for multiple schemas/datasets
        return set(chain(*(schema.enabled_bq_ids for schema in self.enabled_schemas)))

    def get_bq_ids(self):

        # definitive function to map from a fivetran schema object to one or more
        # bigquery schemas with one or more tables
        #
        # an empty return indicates that there is no data in bigquery yet

        service_type = self.conf.service_type

        # event_tracking
        # tables are generated dynamically, bigquery is the source of truth
        if service_type == ServiceTypeEnum.EVENT_TRACKING:
            return get_bq_ids_from_dataset_safe(self.schema_prefix)

        # webhooks or reporting_api
        # only one table, validate it exists
        if service_type in [ServiceTypeEnum.WEBHOOKS, ServiceTypeEnum.REPORTING_API]:
            bq_id = f'{self.schema_prefix}.{self.conf.static_config["table"]}'
            return {bq_id} if check_bq_id_exists(bq_id) else set()

        # api_cloud
        # cross reference fivetran schema and bigquery dataset
        if service_type == ServiceTypeEnum.API_CLOUD:
            # only databases have multiple schemas
            return self.schemas[0].get_bq_ids()

        # database
        # ditto api_cloud but for multiple schemas/datasets
        return set(chain(*(schema.get_bq_ids() for schema in self.enabled_schemas)))


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
