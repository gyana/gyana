from django.utils import timezone

from apps.base import clients
from apps.connectors.fivetran.config import ServiceTypeEnum
from apps.connectors.models import Connector
from apps.integrations.models import Integration


def _delete_tables_not_in_schema(connector: Connector):
    # if we've deleted tables, we'll need to delete them from BigQuery

    schema_obj = clients.fivetran().get_schemas(connector)
    bq_ids = schema_obj.get_bq_ids()

    for table in connector.integration.table_set.all():
        if table.bq_id not in bq_ids:
            table.delete()

    # re-calculate total rows after tables are deleted
    connector.integration.project.team.update_row_count()


def _check_new_tables_added_to_schema(connector: Connector):
    # if we've added new tables, we need to trigger resync
    # otherwise, we don't want to make the user wait

    schema_obj = clients.fivetran().get_schemas(connector)
    bq_ids = schema_obj.get_bq_ids()

    current_bq_ids = {t.bq_id for t in connector.integration.table_set.all()}

    return len(bq_ids - current_bq_ids) > 0


def _start_initial_connector_sync(connector: Connector):

    clients.fivetran().start_initial_sync(connector)

    connector.fivetran_sync_started = timezone.now()
    connector.save()

    connector.integration.state = Integration.State.LOAD
    connector.integration.save()


def _start_update_connector_sync(connector: Connector):

    service_type = connector.conf.service_type

    # it is possible to skip a resync, if the only change is to delete tables
    # from the schema for the api_cloud or database connectors
    requires_resync = True

    if service_type in [
        ServiceTypeEnum.API_CLOUD,
        ServiceTypeEnum.DATABASE,
    ]:
        _delete_tables_not_in_schema(connector)
        requires_resync = _check_new_tables_added_to_schema(connector)

    if requires_resync:
        clients.fivetran().start_update_sync(connector)

        connector.fivetran_sync_started = timezone.now()
        connector.save()

        connector.integration.state = Integration.State.LOAD
        connector.integration.save()


def start_connector_sync(connector: Connector):

    fivetran_obj = clients.fivetran().get(connector)

    if fivetran_obj.status.is_historical_sync:
        return _start_initial_connector_sync(connector)

    return _start_update_connector_sync(connector)
