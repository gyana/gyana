from functools import lru_cache

import yaml

SERVICES = "apps/connectors/fivetran/services.yaml"
METADATA = "apps/connectors/fivetran/metadata.yaml"


@lru_cache
def get_services():
    services = yaml.load(open(SERVICES, "r"))
    metadata = yaml.load(open(METADATA, "r"))

    for service in services:
        services[service] = {**services[service], **metadata.get(service, {})}

    return services


@lru_cache
def get_service_categories(show_internal=False):
    services = get_services()
    service_categories = []

    for service in services:
        if services[service]["type"] not in service_categories and (
            show_internal or services[service].get("internal") != "t"
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
        services = [s for s in services if s.get("internal") != "t"]

    services = sorted(services, key=lambda s: s["name"])

    return services
