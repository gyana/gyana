from .models import Team


def create_team_dataset(team: Team):
    from apps.base.clients import bigquery_client

    client = bigquery_client()
    # exists ok is for testing
    client.create_dataset(team.tables_dataset_id, exists_ok=True)


def delete_team_dataset(team: Team):
    from apps.base.clients import bigquery_client

    client = bigquery_client()
    client.delete_dataset(
        team.tables_dataset_id, delete_contents=True, not_found_ok=True
    )
