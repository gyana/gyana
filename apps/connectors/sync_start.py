from django.utils import timezone

from apps.base import clients
from apps.connectors.models import Connector
from apps.integrations.models import Integration


def _check_new_tables(connector: Connector):
    bq_ids = clients.fivetran().get_schemas(connector).get_bq_ids()
    return len(bq_ids - connector.integration.bq_ids) > 0


def start_connector_sync(connector: Connector):

    fivetran_obj = clients.fivetran().get(connector)

    if fivetran_obj.status.is_historical_sync:
        clients.fivetran().start_initial_sync(connector)
    else:
        # it is possible to skip a resync if no new tables are added and the
        # connector uses a known schema object
        if not connector.conf.service_uses_schema or _check_new_tables(connector):
            clients.fivetran().start_update_sync(connector)

    connector.fivetran_sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()
