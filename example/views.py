import rest_framework.parsers
import rest_framework.renderers
from rest_framework import exceptions

import rest_framework_json_api.metadata
import rest_framework_json_api.parsers
import rest_framework_json_api.renderers
from rest_framework_json_api.pagination import PageNumberPagination
from rest_framework_json_api.utils import format_drf_errors
from rest_framework_json_api.views import ModelViewSet, RelationshipView

from example.models import Author, Blog, Comment, Company, Entry, Project
from example.serializers import (
    AuthorSerializer,
    BlogSerializer,
    CommentSerializer,
    CompanySerializer,
    EntrySerializer,
    ProjectSerializer
)

HTTP_422_UNPROCESSABLE_ENTITY = 422


class BlogViewSet(ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer

    def get_object(self):
        entry_pk = self.kwargs.get('entry_pk', None)
        if entry_pk is not None:
            return Entry.objects.get(id=entry_pk).blog

        return super(BlogViewSet, self).get_object()


class JSONAPIViewSet(ModelViewSet):
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
        response = super(JSONAPIViewSet, self).handle_exception(exc)
        context = self.get_exception_handler_context()
        return format_drf_errors(response, context, exc)


class BlogCustomViewSet(JSONAPIViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer


class EntryViewSet(ModelViewSet):
    queryset = Entry.objects.all()
    resource_name = 'posts'

    def get_serializer_class(self):
        return EntrySerializer

    def get_object(self):
        # Handle featured
        entry_pk = self.kwargs.get('entry_pk', None)
        if entry_pk is not None:
            return Entry.objects.exclude(pk=entry_pk).first()

        return super(EntryViewSet, self).get_object()


class NoPagination(PageNumberPagination):
    page_size = None


class NonPaginatedEntryViewSet(EntryViewSet):
    pagination_class = NoPagination
    ordering_fields = ('headline', 'body_text', 'blog__name', 'blog__id')


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    prefetch_for_includes = {
        '__all__': [],
        'author': ['author__bio', 'author__entries'],
    }

    def get_queryset(self, *args, **kwargs):
        entry_pk = self.kwargs.get('entry_pk', None)
        if entry_pk is not None:
            return self.queryset.filter(entry_id=entry_pk)

        return super(CommentViewSet, self).get_queryset()


class CompanyViewset(ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer


class ProjectViewset(ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer


class EntryRelationshipView(RelationshipView):
    queryset = Entry.objects.all()


class BlogRelationshipView(RelationshipView):
    queryset = Blog.objects.all()


class CommentRelationshipView(RelationshipView):
    queryset = Comment.objects.all()


class AuthorRelationshipView(RelationshipView):
    queryset = Author.objects.all()
    self_link_view_name = 'author-relationships'
