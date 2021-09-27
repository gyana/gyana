from functools import lru_cache

import yaml

SERVICES = "apps/connectors/services.yaml"
METADATA = "apps/connectors/metadata.yaml"


@lru_cache
def get_services():
    services = yaml.load(open(SERVICES, "r"))
    metadata = yaml.load(open(METADATA, "r"))

    for service in services:
        services[service] = {**services[service], **metadata.get(service, {})}

    return services


@lru_cache
def get_service_categories():
    services = get_services()
    service_categories = []

    for service in services:
        if services[service]["type"] not in service_categories:
            service_categories.append(services[service]["type"])

    return service_categories
