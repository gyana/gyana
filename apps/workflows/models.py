from django.db import models
from django.urls import reverse
from model_clone import CloneMixin

from apps.base.models import BaseModel
from apps.projects.models import Project


class Workflow(CloneMixin, BaseModel):
    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    last_run = models.DateTimeField(null=True)
    data_updated = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_workflows:detail", args=(self.project.id, self.id))

    @property
    def failed(self):
        return any(node.error is not None for node in self.nodes.all())

    @property
    def output_nodes(self):
        from apps.nodes.models import Node

        return self.nodes.filter(kind=Node.Kind.OUTPUT)

    @property
    def out_of_date(self):
        if not self.last_run:
            return True

        input_nodes = self.nodes.filter(kind="input").all()
        input_tables = [
            input_node.input_table
            for input_node in input_nodes
            if input_node.input_table
        ]
        if not input_tables:
            return True

        latest_input_update = max(
            input_table.data_updated for input_table in input_tables
        )
        return self.last_run < max(self.data_updated, latest_input_update)
