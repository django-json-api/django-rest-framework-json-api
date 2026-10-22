from django_filters import rest_framework as filters

from rest_framework_json_api.pagination import JsonApiPageNumberPagination
from rest_framework_json_api.views import ModelViewSet, RelationshipView

from example.models import Author, Blog, Comment, Entry, ProjectType, Questionnaire
from example.serializers import (
    AuthorDetailSerializer,
    AuthorListSerializer,
    AuthorSerializer,
    BlogDRFSerializer,
    BlogSerializer,
    CommentSerializer,
    EntryDRFSerializers,
    EntrySerializer,
    ProjectTypeSerializer,
    QuestionnaireSerializer,
)

HTTP_422_UNPROCESSABLE_ENTITY = 422


class BlogViewSet(ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer

    def get_object(self):
        entry_pk = self.kwargs.get("entry_pk", None)
        if entry_pk is not None:
            return Entry.objects.get(id=entry_pk).blog

        return super().get_object()


class DRFBlogViewSet(ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogDRFSerializer
    lookup_url_kwarg = "entry_pk"

    def get_object(self):
        entry_pk = self.kwargs.get(self.lookup_url_kwarg, None)
        if entry_pk is not None:
            return Entry.objects.get(id=entry_pk).blog

        return super().get_object()


class EntryViewSet(ModelViewSet):
    queryset = Entry.objects.all()
    # TODO it should not be supported to overwrite resource name
    # of endpoints with serializers as includes and sparse fields
    # cannot be aware of it
    # resource_name = "posts"

    def get_serializer_class(self):
        return EntrySerializer

    def get_object(self):
        # Handle featured
        entry_pk = self.kwargs.get("entry_pk", None)
        if entry_pk is not None:
            return Entry.objects.exclude(pk=entry_pk).first()

        return super().get_object()


class DRFEntryViewSet(ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntryDRFSerializers
    lookup_url_kwarg = "entry_pk"


class NoPagination(JsonApiPageNumberPagination):
    page_size = None


class NonPaginatedEntryViewSet(EntryViewSet):
    pagination_class = NoPagination
    ordering_fields = ("headline", "body_text", "blog__name", "blog__id")
    rels = (
        "exact",
        "iexact",
        "contains",
        "icontains",
        "gt",
        "gte",
        "lt",
        "lte",
        "in",
        "regex",
        "isnull",
    )
    filterset_fields = {
        "id": ("exact", "in"),
        "headline": rels,
        "body_text": rels,
        "blog__name": rels,
        "blog__tagline": rels,
    }
    search_fields = ("headline", "body_text", "blog__name", "blog__tagline")


class EntryFilter(filters.FilterSet):
    bname = filters.CharFilter(field_name="blog__name", lookup_expr="exact")

    authors__id = filters.ModelMultipleChoiceFilter(
        field_name="authors",
        to_field_name="id",
        conjoined=True,  # to "and" the ids
        queryset=Author.objects.all(),
    )

    class Meta:
        model = Entry
        fields = {
            "id": ("exact",),
            "headline": ("exact",),
            "body_text": ("exact",),
            "authors__id": ("in",),
        }


class FiltersetEntryViewSet(EntryViewSet):
    """
    like above but use filterset_class instead of filterset_fields
    """

    pagination_class = NoPagination
    filterset_fields = None
    filterset_class = EntryFilter


class NoFiltersetEntryViewSet(EntryViewSet):
    """
    like above but no filtersets
    """

    pagination_class = NoPagination
    filterset_fields = None
    filterset_class = None


class AuthorViewSet(ModelViewSet):
    queryset = Author.objects.all()
    filterset_fields = ("author_type", "name")

    def get_serializer_class(self):
        serializer_classes = {
            "list": AuthorListSerializer,
            "retrieve": AuthorDetailSerializer,
        }

        action = getattr(self, "action", "")
        return serializer_classes.get(action, AuthorSerializer)


class CommentViewSet(ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    select_for_includes = {"writer": ["author__bio"]}
    prefetch_for_includes = {
        "__all__": [],
        "author": ["author__bio", "author__entries"],
    }

    def get_queryset(self, *args, **kwargs):
        queryset = super().get_queryset()

        entry_pk = self.kwargs.get("entry_pk", None)
        if entry_pk is not None:
            queryset = queryset.filter(entry_id=entry_pk)

        return queryset


class ProjectTypeViewset(ModelViewSet):
    queryset = ProjectType.objects.all()
    serializer_class = ProjectTypeSerializer


class EntryRelationshipView(RelationshipView):
    queryset = Entry.objects.all()


class BlogRelationshipView(RelationshipView):
    queryset = Blog.objects.all()


class CommentRelationshipView(RelationshipView):
    queryset = Comment.objects.all()


class AuthorRelationshipView(RelationshipView):
    queryset = Author.objects.all()
    self_link_view_name = "author-relationships"


class QuestionnaireViewset(ModelViewSet):
    queryset = Questionnaire.objects.all()
    serializer_class = QuestionnaireSerializer
