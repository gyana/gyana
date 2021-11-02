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
    # webhooks_reports = single table in one schema (no schema provided)
    # event_tracking = dynamic tables in one schema (no schema provided)
    #
    # the fivetran getting started diagram has a good summary of the options
    # https://fivetran.com/docs/getting-started/core-concepts
    # and the rest of the docs cover each service type in detail

    API_CLOUD = "api_cloud"
    DATABASE = "database"
    WEBHOOKS_REPORTS = "webhooks_reports"
    EVENT_TRACKING = "event_tracking"


@dataclass
class Service:
    id: str

    # internal configuration
    service_type: ServiceTypeEnum = "api_cloud"
    static_config: Dict[str, Any] = field(default_factory=dict)
    internal: bool = False

    # fivetran metadata
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


@lru_cache
def get_services_obj():
    services = yaml.load(open(SERVICES, "r"))
    metadata = yaml.load(open(METADATA, "r"))
    return {k: Service(id, **v, **metadata[k]) for k, v in services.items()}


@lru_cache
def get_service_categories(show_internal=False):
    services = get_services_obj()
    return sorted([s.type for s in services if (show_internal or not s.internal)])


def get_services_query(category=None, search=None, show_internal=False):
    services = list(get_services_obj().values())

    if (category := category) is not None:
        services = [s for s in services if s.type == category]

    if (search := search) is not None:
        services = [s for s in services if search.lower() in s.name.lower()]

    if not show_internal:
        services = [s for s in services if not s.internal]

    services = sorted(services, key=lambda s: s.name)

    return services
