from django.urls import reverse

from apps.base.frames import TurboFrameUpdateView

from .forms import ProjectUpdateForm
from .models import Project


class ProjectSettings(TurboFrameUpdateView):
    template_name = "projects/automate_settings.html"
    model = Project
    form_class = ProjectUpdateForm
    turbo_frame_dom_id = "projects:automate_settings"

    def get_success_url(self):
        return reverse("projects:automate_settings", args=(self.project.id,))
