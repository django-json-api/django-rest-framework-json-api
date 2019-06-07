from django.contrib.auth import models as auth_models
from django.utils import encoding
from rest_framework import generics, parsers, renderers, serializers, viewsets
from rest_framework.response import Response

from rest_framework_json_api import mixins, utils

from ..serializers.identity import IdentitySerializer
from ..serializers.post import PostSerializer

try:
    from rest_framework.decorators import action

    def detail_route(**kwargs):
        return action(detail=True, **kwargs)

    def list_route(**kwargs):
        return action(detail=False, **kwargs)

except ImportError:
    from rest_framework.decorators import detail_route, list_route


class Identity(mixins.MultipleIDMixin, viewsets.ModelViewSet):
    queryset = auth_models.User.objects.all().order_by('pk')
    serializer_class = IdentitySerializer

    # demonstrate sideloading data for use at app boot time
    @list_route()
    def posts(self, request):
        self.resource_name = False

        identities = self.queryset
        posts = [{'id': 1, 'title': 'Test Blog Post'}]

        data = {
            encoding.force_text('identities'): IdentitySerializer(identities, many=True).data,
            encoding.force_text('posts'): PostSerializer(posts, many=True).data,
        }
        return Response(utils.format_field_names(data, format_type='camelize'))

    @detail_route()
    def manual_resource_name(self, request, *args, **kwargs):
        self.resource_name = 'data'
        return super(Identity, self).retrieve(request, args, kwargs)

    @detail_route()
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
