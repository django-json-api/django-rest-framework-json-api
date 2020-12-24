from rest_framework_json_api.views import ModelViewSet, RelationshipView

from .models import BasicModel


class BasicModelViewSet(ModelViewSet):
    class Meta:
        model = BasicModel


class BasicModelRelationshipView(RelationshipView):
    queryset = BasicModel.objects
