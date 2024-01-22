from apps.base.forms import ModelForm

from .models import {{ cookiecutter.model_name }}


class {{ cookiecutter.model_name }}Form(ModelForm):
    class Meta:
        model = {{ cookiecutter.model_name }}
        fields = ['name']
