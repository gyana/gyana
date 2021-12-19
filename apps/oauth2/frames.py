from django_tables2 import SingleTableMixin

from apps.base.frames import TurboFrameListView
from apps.projects.mixins import ProjectMixin

from .models import OAuth2
from .tables import OAuth2Table


class OAuth2List(ProjectMixin, SingleTableMixin, TurboFrameListView):
    template_name = "oauth2/list.html"
    model = OAuth2
    table_class = OAuth2Table
    paginate_by = 20
    turbo_frame_dom_id = "oauth2:list"

    def get_queryset(self):
        return self.project.oauth2_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["oauth2_count"] = self.project.oauth2_set.count()
        return context
