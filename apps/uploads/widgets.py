from django.forms.widgets import FileInput


class GCSFileUpload(FileInput):
    class Media:
        js = ("js/components-bundle.js",)

    template_name = "django/forms/widgets/gcs_file_upload.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        context["widget"]["name"] = name
        # context["widget"]["accept"] = attrs["accept"]
        return context
