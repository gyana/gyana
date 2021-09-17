from django.forms.widgets import Select


class SelectWithDisable(Select):
    def __init__(
        self,
        disabled,
        attrs=None,
        choices=(),
    ) -> None:
        super().__init__(attrs=attrs, choices=choices)
        self.disabled = disabled

    def get_context(self, name, value, attrs):

        context = super().get_context(name, value, attrs)
        for _, optgroup, __ in context["widget"]["optgroups"]:
            for option in optgroup:
                if (value := option["value"]) in self.disabled:
                    option["attrs"]["disabled"] = True
                    option["attrs"]["title"] = self.disabled[value]
        return context
