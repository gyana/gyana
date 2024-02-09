from django.forms.widgets import Select, Textarea


class CodeMirror(Textarea):
    template_name = "django/forms/widgets/codemirror.html"

    def __init__(self, schema) -> None:
        self.schema = schema
        super().__init__()

    def get_context(self, name: str, value, attrs):
        context = super().get_context(name, value, attrs)
        context["columns"] = list(self.schema)
        return context
