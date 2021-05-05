from apps.dataflows.nodes import NODE_FROM_CONFIG
from apps.datasets.models import Dataset
from apps.projects.models import Project
from django.db import models


class Dataflow(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ("-created",)

    def __str__(self):
        return self.name


class Node(models.Model):
    class Kind(models.TextChoices):
        INPUT = "input", "Input"
        JOIN = "join", "Join"

    dataflow = models.ForeignKey(Dataflow, on_delete=models.CASCADE)
    kind = models.CharField(max_length=16, choices=Kind.choices)
    x = models.FloatField()
    y = models.FloatField()
    parents = models.ManyToManyField(
        "self", symmetrical=False, related_name="children", blank=True
    )
    _input_dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, null=True)
    _join_how = models.CharField(
        max_length=12,
        choices=[
            ("inner", "Inner"),
            ("outer", "Outer"),
            ("left", "Left"),
            ("right", "Right"),
        ],
        default="inner",
    )
    _join_left = models.CharField(max_length=300, null=True, blank=True)
    _join_right = models.CharField(max_length=300, null=True, blank=True)

    def get_query(self):
        func = NODE_FROM_CONFIG[self.kind]
        return func(self)

    def get_schema(self):
        return self.get_query().schema()
