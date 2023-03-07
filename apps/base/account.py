def is_scheduled_help_text(is_scheduled_field, project):
    is_scheduled_field.help_text = (
        f"Daily at {project.daily_schedule_time} in {project.team.timezone}"
    )
