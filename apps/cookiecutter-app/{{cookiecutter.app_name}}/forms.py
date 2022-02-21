from apps.base.forms import BaseModelForm

from .models import {{ cookiecutter.model_name }}


class {{ cookiecutter.model_name }}Form(BaseModelForm):
    class Meta:
        model = {{ cookiecutter.model_name }}
        fields = ['name']
