from django.conf.urls import re_path
from rest_framework.routers import SimpleRouter

from .views import BasicModelRelationshipView, BasicModelViewSet

router = SimpleRouter()
router.register(r"basic_models", BasicModelViewSet, basename="basic-model")

urlpatterns = [
    re_path(
        r"^basic_models/(?P<pk>[^/.]+)/(?P<related_field>[^/.]+)/$",
        BasicModelViewSet.as_view({"get": "retrieve_related"}),
        name="basic-model-related",
    ),
    re_path(
        r"^basic_models/(?P<pk>[^/.]+)/relationships/(?P<related_field>[^/.]+)/$",
        BasicModelRelationshipView.as_view(),
        name="basic-model-relationships",
    ),
]

urlpatterns += router.urls
