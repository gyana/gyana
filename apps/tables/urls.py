from rest_framework import routers

from . import rest

app_name = "tables"

urlpatterns = []

router = routers.DefaultRouter()
router.register("api/tables", rest.TableViewSet, basename="Table")
urlpatterns += router.urls
