from rest_framework_json_api.views import ModelViewSet
from tests.models import (
    BasicModel,
    ForeignKeySource,
    ForeignKeyTarget,
    ManyToManySource,
    NestedRelatedSource,
)
from tests.serializers import (
    BasicModelSerializer,
    ForeignKeySourceSerializer,
    ForeignKeySourcetHyperlinkedSerializer,
    ForeignKeyTargetSerializer,
    ManyToManySourceSerializer,
    NestedRelatedSourceSerializer,
)


class BasicModelViewSet(ModelViewSet):
    serializer_class = BasicModelSerializer
    queryset = BasicModel.objects.all()
    ordering = ["text"]


class ForeignKeySourceViewSet(ModelViewSet):
    serializer_class = ForeignKeySourceSerializer
    queryset = ForeignKeySource.objects.all()
    ordering = ["name"]


class ForeignKeySourcetHyperlinkedViewSet(ModelViewSet):
    serializer_class = ForeignKeySourcetHyperlinkedSerializer
    queryset = ForeignKeySource.objects.all()
    ordering = ["name"]


class ForeignKeyTargetViewSet(ModelViewSet):
    serializer_class = ForeignKeyTargetSerializer
    queryset = ForeignKeyTarget.objects.all()
    ordering = ["name"]


class ManyToManySourceViewSet(ModelViewSet):
    serializer_class = ManyToManySourceSerializer
    queryset = ManyToManySource.objects.all()
    ordering = ["name"]


class NestedRelatedSourceViewSet(ModelViewSet):
    serializer_class = NestedRelatedSourceSerializer
    queryset = NestedRelatedSource.objects.all()
    ordering = ["id"]
