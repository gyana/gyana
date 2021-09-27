from apps.projects.models import Project
from django.db.models import BooleanField, Case, Value, When
from django.forms.widgets import SelectMultiple


class MemberSelect(SelectMultiple):
    template_name = "projects/_member_select.html"
    current_user = None

    def get_context(self, name: str, value, attrs):
        context = super().get_context(name, value, attrs)
        # For some reason when changing from everyone to invite, value can contain an empty list
        value = value if len(value) > 0 and not isinstance(value[0], list) else []
        context["users"] = self.choices.queryset.annotate(
            is_current_user=Case(
                When(id=self.current_user.id, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
            is_project_member=Case(
                When(id__in=value, then=Value(True)),
                default=Value(False),
                output_field=BooleanField(),
            ),
        ).order_by("-is_current_user", "-is_project_member", "email")
        return context

    def use_required_attribute(self, initial):
        # Don't use the 'required' attribute because browser validation would
        # require all checkboxes to be checked instead of at least one.
        return False
