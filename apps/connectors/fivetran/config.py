from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Dict

import yaml

SERVICES = "apps/connectors/fivetran/services.yaml"
METADATA = "apps/connectors/fivetran/metadata.yaml"


class ServiceTypeEnum(Enum):

    # api_cloud = fixed tables in one schema
    # database = fixed tables in multiple schemas
    # webhooks = single dynamic table in one schema (no schema provided)
    # reporting_api = single fixed table in one schema (no schema provided)
    # event_tracking = dynamic tables in one schema (no schema provided)
    #
    # the fivetran getting started diagram has a good summary of the options
    # https://fivetran.com/docs/getting-started/core-concepts
    # and the rest of the docs cover each service type in detail

    API_CLOUD = "api_cloud"
    DATABASE = "database"
    WEBHOOKS = "webhooks"
    REPORTING_API = "reporting_api"
    EVENT_TRACKING = "event_tracking"


@dataclass
class Service:
    # internal configuration
    service_type: ServiceTypeEnum = "api_cloud"
    static_config: Dict[str, Any] = field(default_factory=dict)
    internal: bool = False

    # fivetran metadata
    id: str = ""
    description: str = ""
    icon_path: str = ""
    icon_url: str = ""
    id: str = ""
    link_to_docs: str = ""
    link_to_erd: str = ""
    name: str = ""
    type: str = ""

    def __post_init__(self):
        self.service_type = ServiceTypeEnum(self.service_type)

    @property
    def service_is_dynamic(self):
        # the tables are not available until an initial event is sent and synced
        return self.service_type in {
            ServiceTypeEnum.WEBHOOKS,
            ServiceTypeEnum.EVENT_TRACKING,
        }

    @property
    def service_uses_schema(self):
        # the tables can be managed via the fivetran schema object
        return self.service_type in {
            ServiceTypeEnum.API_CLOUD,
            ServiceTypeEnum.DATABASE,
        }


@lru_cache
def get_services_obj():
    services = yaml.load(open(SERVICES, "r"))
    metadata = yaml.load(open(METADATA, "r"))
    return {k: Service(**v, **metadata[k]) for k, v in services.items()}


@lru_cache
def get_service_categories(show_internal=False):
    services = get_services_obj()
    categories = [
        s.type for s in services.values() if (show_internal or not s.internal)
    ]
    return sorted(list(set(categories)))


def get_services_query(category=None, search=None, show_internal=False):
    services = list(get_services_obj().values())

    if category is not None:
        services = [s for s in services if s.type == category]

    if search is not None:
        services = [s for s in services if search.lower() in s.name.lower()]

    if not show_internal:
        services = [s for s in services if not s.internal]

    services = sorted(services, key=lambda s: s.name)

    return services
