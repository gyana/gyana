from django.forms.widgets import ChoiceWidget, Textarea

ICONS = {"integration": "far fa-link", "workflow_node": "far fa-stream"}


class SourceSelect(ChoiceWidget):
    class Media:
        js = ("js/templates-bundle.js",)

    template_name = "django/forms/widgets/select_source.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["options"] = [
            {"icon": ICONS[option.source], "id": option.id, "label": option.owner_name}
            for option in self.choices.queryset
        ]

        context["widget"]["selected"] = value
        context["widget"]["name"] = name
        return context


class InputNode(SourceSelect):
    template_name = "django/forms/widgets/input_node.html"


class CodeMirror(Textarea):
    template_name = "django/forms/widgets/codemirror.html"
