from django.core.exceptions import ValidationError

from apps.base.forms import BaseModelForm
from apps.users.models import CustomUser

from .models import Invite


class InviteForm(BaseModelForm):
    class Meta:
        model = Invite
        fields = ["email", "role"]

    def __init__(self, *args, **kwargs) -> None:
        self.team = kwargs.pop("team")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        email = cleaned_data.get("email")

        if user := CustomUser.objects.filter(email=email).first():
            if self.team in user.teams.all():
                raise ValidationError(
                    "A user with this email is already part of your team."
                )

        if Invite.objects.filter(team=self.team, email=email, accepted=False).exists():
            raise ValidationError(
                "A user with this email is already invited to your team."
            )

        return cleaned_data


class InviteUpdateForm(BaseModelForm):
    class Meta:
        model = Invite
        fields = ["email", "role"]
