from functools import cached_property

from apps.base.frames import TurboFrameCreateView
from apps.exports.tasks import export_to_gcs
from apps.nodes.models import Node
from django.urls.base import reverse

from .forms import ExportForm
from .models import Export


class ExportCreate(TurboFrameCreateView):
    template_name = "exports/create.html"
    model = Export
    fields = []
    turbo_frame_dom_id = "export-create"

    @cached_property
    def node(self):
        return Node.objects.get(pk=self.kwargs["parent_id"])

    def form_valid(self, form):
        form.instance.node = self.node
        form.instance.save()

        export_to_gcs(form.instance, self.request.user)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parent_id"] = self.node.id
        return context

    def get_success_url(self) -> str:
        return reverse("exports:create", args=(self.node.id,))
