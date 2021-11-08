def get_subscriber_by_payload(team_model, payload):
    team_id = payload["team_id"]
    team = team_model.objects.filter(pk=team_id).first()

    if team is not None:
        return team
