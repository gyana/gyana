from django.forms.widgets import ChoiceWidget


class ConnectorSchemaMultiSelect(ChoiceWidget):
    template_name = "django/forms/widgets/multiple_input.html"
    option_template_name = "connectors/widgets/connector_table_option.html"
    allow_multiple_selected = True

    def create_option(self, name, value, *args, **kwargs):
        # inspired by https://djangosnippets.org/snippets/10646/
        option_dict = super().create_option(name, value, *args, **kwargs)
        enabled_patch_settings = self._schema_dict[value].enabled_patch_settings
        if not enabled_patch_settings["allowed"]:
            option_dict["attrs"]["disabled"] = "disabled"
            option_dict["reason"] = enabled_patch_settings.get("reason")
        return option_dict

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False
