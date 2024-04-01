from django.http import FileResponse
from django.views.generic import DetailView

from .models import Export


class ExportDownload(DetailView):
    model = Export

    def get(self, request, *args, **kwargs):
        object = self.get_object()
        res = FileResponse(object.file)
        res["Content-Type"] = "application/octet-stream"
        res["Content-Disposition"] = f'attachment; filename="{object.file.name}"'
        return res
