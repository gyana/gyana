from django import forms
from django.forms.models import BaseInlineFormSet


class BaseInlineFormset(BaseInlineFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["DELETE"].widget = forms.HiddenInput()


class RequiredInlineFormset(BaseInlineFormset):
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

    def save_new_objects(self, commit=True):
        """Overwrites Django's BaseModelFormSet that doesnt save an instance of
        a formset form if the initial values haven't changed."""
        self.new_objects = []
        for form in self.extra_forms:
            # If someone has marked an add form for deletion, don't save the
            # object.
            if self.can_delete and self._should_delete_form(form):
                continue
            self.new_objects.append(self.save_new(form, commit=commit))
            if not commit:
                self.saved_forms.append(form)
        return self.new_objects
