from functools import lru_cache

import yaml
from django.conf import settings

SERVICES = "apps/connectors/services.yaml"


@lru_cache
def get_services():
    return {key: val for key, val in yaml.load(open(SERVICES, "r")).items()}


@lru_cache
def get_service_categories():
    services = get_services()
    service_categories = []

    for service in services:
        if services[service]["category"] not in service_categories:
            service_categories.append(services[service]["category"])

    return service_categories
