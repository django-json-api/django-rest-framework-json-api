"""
Test Serializer and Resource
"""
from django.contrib.auth import models as auth_models

from rest_framework import serializers, generics, viewsets
from rest_framework.response import Response

from rest_framework_ember import renderers, parsers, mixins


class IdentitySerializer(serializers.ModelSerializer):
    """
    Identity Serializer
    """
    class Meta:
        model = auth_models.User
        fields = (
            'id', 'first_name', 'last_name', 'email', )


class CarSerializer(serializers.Serializer):
    """
    Cars serializer
    """
    name = serializers.CharField(max_length=50)


class UserCarSerializer(serializers.Serializer):
    """
    Serializer that returns a list of users & cars.
    """
    users = IdentitySerializer(many=True)
    cars = CarSerializer(many=True)


class User(generics.GenericAPIView):
    """
    Current user's identity endpoint.

    GET /me
    """
    serializer_class = IdentitySerializer
    allowed_methods = ['GET']

    def get_queryset(self):
        return auth_models.User.objects.all()

    def get(self, request, pk=None):
        """
        GET request
        """
        obj = self.get_object()
        serializer = self.serializer_class(obj)
        return Response(serializer.data)


class UserEmber(User):
    """
    Use the rest_framework_ember Renderer/Parser
    """
    resource_name = 'data'

    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.JSONParser, )


class EmberUserModelViewSet(viewsets.ModelViewSet):
    queryset = auth_models.User.objects.all()
    serializer_class = IdentitySerializer
    allowed_methods = ['GET', 'POST', 'PUT', ]
    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.JSONParser, )


class MultipleIDMixinUserModelViewSet(mixins.MultipleIDMixin,
                                     EmberUserModelViewSet):

    queryset = auth_models.User.objects.all()


class UserCarResource(UserEmber):
    """
    Resource that returns a list of users and cars.
    """
    resource_name = False

    cars = [
        {'id': 1, 'name': 'BMW'},
        {'id': 2, 'name': 'Mercedes'},
        {'id': 3, 'name': 'Mini'},
        {'id': 4, 'name': 'Ford'}
    ]

    def get(self, request, *args, **kwargs):
        data = {
            'users': self.get_queryset(),
            'cars': self.cars
        }
        serializer = UserCarSerializer(data)
        return Response(serializer.data)

