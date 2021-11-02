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
    service_type: ServiceTypeEnum = "api_cloud"
    static_config: Dict[str, Any] = field(default_factory=dict)
    internal: bool = False

    def __post_init__(self):
        self.service_type = ServiceTypeEnum(self.service_type)


@lru_cache
def get_services():
    services = yaml.load(open(SERVICES, "r"))
    metadata = yaml.load(open(METADATA, "r"))

    for service in services:
        services[service] = {**services[service], **metadata.get(service, {})}

    return services


@lru_cache
def get_services_obj():

    services = yaml.load(open(SERVICES, "r"))

    return {k: Service(**v) for k, v in services.items()}


@lru_cache
def get_service_categories(show_internal=False):
    services = get_services()
    service_categories = []

    for service in services:
        if services[service]["type"] not in service_categories and (
            show_internal or not services[service].get("internal")
        ):
            service_categories.append(services[service]["type"])

    return service_categories


def get_services_query(category=None, search=None, show_internal=False):
    services = list(get_services().values())

    if (category := category) is not None:
        services = [s for s in services if s["type"] == category]

    if (search := search) is not None:
        services = [s for s in services if search.lower() in s["name"].lower()]

    if not show_internal:
        services = [s for s in services if not s.get("internal")]

    services = sorted(services, key=lambda s: s["name"])

    return services
