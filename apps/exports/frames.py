from functools import cached_property

from django.urls.base import reverse

from apps.base.frames import TurboFrameCreateView
from apps.exports.tasks import export_to_gcs
from apps.nodes.models import Node
from apps.tables.models import Table

from .forms import ExportForm
from .models import Export


class ExportCreate(TurboFrameCreateView):
    template_name = "exports/create.html"
    model = Export
    fields = []
    turbo_frame_dom_id = "exports:create"

    @cached_property
    def node(self):
        return Node.objects.get(pk=self.kwargs["parent_id"])

    @cached_property
    def integration_table(self):
        return Table.objects.get(pk=self.kwargs["parent_id"])

    @property
    def parent(self):
        if self.kwargs["parent_type"] == "node":
            return self.node
        return self.integration_table

    def form_valid(self, form):
        export = form.instance
        if self.kwargs["parent_type"] == "node":
            export.node = self.node
        else:
            export.integration_table = self.integration_table
        export.save()

        export_to_gcs.delay(export.id, self.request.user.id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["parent_id"] = self.parent.id
        context["parent_type"] = self.kwargs["parent_type"]
        # Get context should only be called when triggered after the click
        context["show_alert"] = True
        return context

    def get_success_url(self) -> str:
        return reverse(
            "exports:create",
            args=(
                self.kwargs["parent_type"],
                self.parent.id,
            ),
        )
