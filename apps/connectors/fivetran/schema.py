from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

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
        res.pop("service_type")
        res.pop("schema_prefix")
        return res

    @property
    def display_name(self):
        return self.name_in_destination.replace("_", " ").title()

    @property
    def enabled_table_ids(self):
        return {table.name_in_destination for table in self.tables if table.enabled}


class FivetranSchemaObj:
    def __init__(self, schemas_dict, service_conf, schema_prefix):
        self.conf = service_conf
        self.schema_prefix = schema_prefix
        self.schemas = [FivetranSchema(key=k, **s) for k, s in schemas_dict.items()]

    def to_dict(self):
        return {s.key: s.asdict() for s in self.schemas}

    @property
    def enabled_schemas(self):
        # the user can has the option to disable individual schemas
        return [s for s in self.schemas if s.enabled]


def update_schema_from_cleaned_data(connector, cleaned_data):
    # mutate the schema_obj based on cleaned_data

    schema_obj = connector.schema_obj

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

    return schema_obj
