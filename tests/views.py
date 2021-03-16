from rest_framework_json_api.views import ModelViewSet
from tests.models import BasicModel
from tests.serializers import BasicModelSerializer


class BasicModelViewSet(ModelViewSet):
    serializer_class = BasicModelSerializer

    class Meta:
        model = BasicModel
