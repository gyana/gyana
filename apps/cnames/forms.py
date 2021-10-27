from django.core.exceptions import NON_FIELD_ERRORS
from django.forms.forms import NON_FIELD_ERRORS

from apps.base.forms import BaseModelForm

from .heroku import create_heroku_domain
from .models import CName


class CNameForm(BaseModelForm):
    class Meta:
        model = CName
        fields = ["domain"]
        help_texts = {"domain": "e.g. dashboards.mycompany.com"}

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team")
        return super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.team = self._team

    def post_save(self, instance):
        create_heroku_domain(instance)

    def is_valid(self) -> bool:
        # Add a non_field_error according to https://stackoverflow.com/a/8598842
        # must call self.errors via is_valid first
        is_valid = super().is_valid()
        if not self._team.can_create_cname:
            errors = self.error_class(
                ["You cannot create more custom domains on your current plan."]
            )
            self._errors[NON_FIELD_ERRORS] = errors
            return False
        return is_valid
