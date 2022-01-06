from django.forms.widgets import CheckboxSelectMultiple


class FlagCheckboxSelectMultiple(CheckboxSelectMultiple):
    template_name = "django/forms/widgets/multiple_input.html"
    option_template_name = "flags/widgets/flag_option.html"
