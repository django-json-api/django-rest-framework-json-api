from rest_framework import exceptions
from rest_framework import viewsets
import rest_framework.parsers
import rest_framework.renderers
import rest_framework_json_api.metadata
import rest_framework_json_api.parsers
import rest_framework_json_api.renderers
from rest_framework_json_api.views import RelationshipView
from example.models import Blog, Entry, Author, Comment
from example.serializers import (
    BlogSerializer, EntrySerializer, AuthorSerializer, CommentSerializer)

from rest_framework_json_api.utils import format_drf_errors

HTTP_422_UNPROCESSABLE_ENTITY = 422


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer


class JsonApiViewSet(viewsets.ModelViewSet):
    """
    This is an example on how to configure DRF-jsonapi from
    within a class. It allows using DRF-jsonapi alongside
    vanilla DRF API views.
    """
    parser_classes = [
        rest_framework_json_api.parsers.JSONParser,
        rest_framework.parsers.FormParser,
        rest_framework.parsers.MultiPartParser,
    ]
    renderer_classes = [
        rest_framework_json_api.renderers.JSONRenderer,
        rest_framework.renderers.BrowsableAPIRenderer,
    ]
    metadata_class = rest_framework_json_api.metadata.JSONAPIMetadata

    def handle_exception(self, exc):
        if isinstance(exc, exceptions.ValidationError):
            # some require that validation errors return 422 status
            # for example ember-data (isInvalid method on adapter)
            exc.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        # exception handler can't be set on class so you have to
        # override the error response in this method
        response = super(JsonApiViewSet, self).handle_exception(exc)
        context = self.get_exception_handler_context()
        return format_drf_errors(response, context, exc)


class BlogCustomViewSet(JsonApiViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    resource_name = 'posts'

    def get_serializer_class(self):
        return EntrySerializer


class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class EntryRelationshipView(RelationshipView):
    queryset = Entry.objects.all()


class BlogRelationshipView(RelationshipView):
    queryset = Blog.objects.all()


class CommentRelationshipView(RelationshipView):
    queryset = Comment.objects.all()


class AuthorRelationshipView(RelationshipView):
    queryset = Author.objects.all()
    self_link_view_name = 'author-relationships'
