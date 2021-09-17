from django.forms.widgets import ChoiceWidget


class ConnectorSchemaMultiSelect(ChoiceWidget):
    template_name = "django/forms/widgets/multiple_input.html"
    option_template_name = "connectors/widgets/connector_table_option.html"
    allow_multiple_selected = True

    def __init__(self, *args, **kwargs):
        self._disabled_choices = []
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, *args, **kwargs):
        option_dict = super().create_option(name, value, *args, **kwargs)
        if value in self._disabled_choices:
            option_dict["attrs"]["disabled"] = "disabled"
        return option_dict

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False
