from django.core.exceptions import ValidationError

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

    def clean(self):
        if not self._team.can_create_cname:
            raise ValidationError(
                "You cannot create more custom domains on your current plan."
            )
        return super().clean()
