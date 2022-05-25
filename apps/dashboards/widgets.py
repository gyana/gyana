from django.forms.widgets import Textarea


class TextareaCode(Textarea):
    template_name = "django/forms/widgets/code.html"
