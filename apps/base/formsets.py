from django.forms.models import BaseInlineFormSet


class RequiredInlineFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.names = kwargs.pop("names", None)
        self.max_num = kwargs.pop("max_num", self.max_num)
        self.min_num = kwargs.pop("min_num", self.min_num)
        super().__init__(*args, **kwargs)
        self.can_add = self.total_form_count() < self.max_num
        self.hide_delete_button = self.min_num == self.max_num

        for form in self.forms:
            form.empty_permitted = False
            form.use_required_attribute = True

    def initial_form_count(self):
        """Return the number of forms that are required in this FormSet."""
        if not self.is_bound:
            # We want to limit the provided forms right now important
            # for the JoinNode that can have more formset forms because we dont
            # delete the relationship if a user is removing an edge
            # but we don't want to render more than necessary
            return min(len(self.get_queryset()), self.max_num)
        return super().initial_form_count()
