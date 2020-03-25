from django.contrib.auth import models as auth_models
from django.utils import encoding
from rest_framework import generics, parsers, renderers, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_json_api import utils

from example.api.serializers.identity import IdentitySerializer
from example.api.serializers.post import PostSerializer


class Identity(viewsets.ModelViewSet):
    queryset = auth_models.User.objects.all().order_by('pk')
    serializer_class = IdentitySerializer

    # demonstrate sideloading data for use at app boot time
    @action(detail=False)
    def posts(self, request):
        self.resource_name = False

        identities = self.queryset
        posts = [{'id': 1, 'title': 'Test Blog Post'}]

        data = {
            encoding.force_str('identities'): IdentitySerializer(identities, many=True).data,
            encoding.force_str('posts'): PostSerializer(posts, many=True).data,
        }
        return Response(utils.format_field_names(data, format_type='camelize'))

    @action(detail=True)
    def manual_resource_name(self, request, *args, **kwargs):
        self.resource_name = 'data'
        return super(Identity, self).retrieve(request, args, kwargs)

    @action(detail=True)
    def validation(self, request, *args, **kwargs):
        raise serializers.ValidationError('Oh nohs!')


class GenericIdentity(generics.GenericAPIView):
    """
    An endpoint that uses DRF's default format so we can test that.

    GET /identities/generic
    """
    serializer_class = IdentitySerializer
    allowed_methods = ['GET']
    renderer_classes = (renderers.JSONRenderer, )
    parser_classes = (parsers.JSONParser, )

    def get_queryset(self):
        return auth_models.User.objects.all()

    def get(self, request, pk=None):
        """
        GET request
        """
        obj = self.get_object()
        return Response(IdentitySerializer(obj).data)
