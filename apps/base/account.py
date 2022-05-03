from django.urls import reverse
from django.utils.html import mark_safe


def is_scheduled_paid_only(is_scheduled_field, project):
    if project.team.is_free:
        is_scheduled_field.disabled = True
        is_scheduled_field.help_text = mark_safe(
            f'Scheduling is only available on a paid plan <a class="link" href="{reverse("teams:pricing", args=(project.team.id, ))}" data-turbo-frame="_top">learn more</a>'
        )
    else:
        is_scheduled_field.help_text = (
            f"Daily at {project.daily_schedule_time} in {project.team.timezone}"
        )
