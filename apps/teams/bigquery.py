from apps.base.clients import bigquery_client

from .models import Team


def create_team_dataset(team: Team):
    client = bigquery_client()
    # exists ok is for testing
    client.create_dataset(team.tables_dataset_id, exists_ok=True)
