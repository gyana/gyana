from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Dict

import yaml

SERVICES = "apps/connectors/fivetran/services.yaml"
METADATA = "apps/connectors/fivetran/metadata.yaml"


class ServiceTypeEnum(Enum):
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
            show_internal or services[service].get("internal")
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
        services = [s for s in services if s.get("internal")]

    services = sorted(services, key=lambda s: s["name"])

    return services
