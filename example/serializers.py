from datetime import datetime

from rest_framework import fields as drf_fields
from rest_framework import serializers as drf_serilazers

from rest_framework_json_api import relations, serializers

from example.models import (
    ArtProject,
    Author,
    AuthorBio,
    AuthorBioMetadata,
    AuthorType,
    Blog,
    Comment,
    Company,
    Entry,
    LabResults,
    Project,
    ProjectType,
    ResearchProject,
    TaggedItem,
)


class TaggedItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaggedItem
        fields = ("tag",)


class TaggedItemDRFSerializer(drf_serilazers.ModelSerializer):
    """
    DRF default serializer to test default DRF functionalities
    """

    class Meta:
        model = TaggedItem
        fields = ("tag",)


class BlogSerializer(serializers.ModelSerializer):
    copyright = serializers.SerializerMethodField()
    tags = relations.ResourceRelatedField(many=True, read_only=True)

    included_serializers = {
        "tags": "example.serializers.TaggedItemSerializer",
    }

    def get_copyright(self, resource):
        return datetime.now().year

    def get_root_meta(self, resource, many):
        return {"api_docs": "/docs/api/blogs"}

    class Meta:
        model = Blog
        fields = ("name", "url", "tags")
        read_only_fields = ("tags",)
        meta_fields = ("copyright",)


class BlogDRFSerializer(drf_serilazers.ModelSerializer):
    """
    DRF default serializer to test default DRF functionalities
    """

    copyright = serializers.SerializerMethodField()
    tags = TaggedItemDRFSerializer(many=True, read_only=True)

    def get_copyright(self, resource):
        return datetime.now().year

    def get_root_meta(self, resource, many):
        return {"api_docs": "/docs/api/blogs"}

    class Meta:
        model = Blog
        fields = ("name", "url", "tags", "copyright")
        read_only_fields = ("tags",)
        meta_fields = ("copyright",)


class EntrySerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # to make testing more concise we'll only output the
        # `featured` field when it's requested via `include`
        request = kwargs.get("context", {}).get("request")
        if request and "featured" not in request.query_params.get("include", []):
            self.fields.pop("featured", None)

    included_serializers = {
        "authors": "example.serializers.AuthorSerializer",
        "comments": "example.serializers.CommentSerializer",
        "featured": "example.serializers.EntrySerializer",
        "suggested": "example.serializers.EntrySerializer",
        "tags": "example.serializers.TaggedItemSerializer",
    }

    body_format = serializers.SerializerMethodField()
    # single related from model
    blog_hyperlinked = relations.HyperlinkedRelatedField(
        related_link_view_name="entry-blog",
        related_link_url_kwarg="entry_pk",
        self_link_view_name="entry-relationships",
        read_only=True,
        source="blog",
    )
    # many related from model
    comments = relations.ResourceRelatedField(many=True, read_only=True)
    # many related hyperlinked from model
    comments_hyperlinked = relations.HyperlinkedRelatedField(
        related_link_view_name="entry-comments",
        related_link_url_kwarg="entry_pk",
        self_link_view_name="entry-relationships",
        many=True,
        read_only=True,
        source="comments",
    )
    # many related from serializer
    suggested = relations.SerializerMethodResourceRelatedField(
        related_link_view_name="entry-suggested",
        related_link_url_kwarg="entry_pk",
        self_link_view_name="entry-relationships",
        model=Entry,
        many=True,
    )
    # many related hyperlinked from serializer
    suggested_hyperlinked = relations.SerializerMethodHyperlinkedRelatedField(
        related_link_view_name="entry-suggested",
        related_link_url_kwarg="entry_pk",
        self_link_view_name="entry-relationships",
        model=Entry,
        many=True,
    )
    # single related from serializer
    featured = relations.SerializerMethodResourceRelatedField(model=Entry)
    # single related hyperlinked from serializer
    featured_hyperlinked = relations.SerializerMethodHyperlinkedRelatedField(
        related_link_view_name="entry-featured",
        related_link_url_kwarg="entry_pk",
        self_link_view_name="entry-relationships",
        model=Entry,
        read_only=True,
    )
    tags = relations.ResourceRelatedField(many=True, read_only=True)

    def get_suggested(self, obj):
        return Entry.objects.exclude(pk=obj.pk)

    def get_featured(self, obj):
        return Entry.objects.exclude(pk=obj.pk).first()

    def get_body_format(self, obj):
        return "text"

    class Meta:
        model = Entry
        fields = (
            "blog",
            "blog_hyperlinked",
            "headline",
            "body_text",
            "pub_date",
            "mod_date",
            "authors",
            "comments",
            "comments_hyperlinked",
            "featured",
            "suggested",
            "suggested_hyperlinked",
            "tags",
            "featured_hyperlinked",
        )
        read_only_fields = ("tags",)
        meta_fields = ("body_format",)

    class JSONAPIMeta:
        included_resources = ["comments"]


class EntryDRFSerializers(drf_serilazers.ModelSerializer):

    tags = TaggedItemDRFSerializer(many=True, read_only=True)
    url = drf_serilazers.HyperlinkedIdentityField(
        view_name="drf-entry-blog-detail",
        lookup_url_kwarg="entry_pk",
        read_only=True,
    )

    class Meta:
        model = Entry
        fields = (
            "tags",
            "url",
        )
        read_only_fields = ("tags",)


class AuthorTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorType
        fields = ("name",)


class AuthorBioSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorBio
        fields = ("author", "body", "metadata")

    included_serializers = {
        "metadata": "example.serializers.AuthorBioMetadataSerializer",
    }


class AuthorBioMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuthorBioMetadata
        fields = ("body",)


class AuthorSerializer(serializers.ModelSerializer):
    bio = relations.ResourceRelatedField(
        related_link_view_name="author-related",
        self_link_view_name="author-relationships",
        queryset=AuthorBio.objects,
    )
    entries = relations.ResourceRelatedField(
        related_link_view_name="author-related",
        self_link_view_name="author-relationships",
        queryset=Entry.objects,
        many=True,
    )
    first_entry = relations.SerializerMethodResourceRelatedField(
        related_link_view_name="author-related",
        self_link_view_name="author-relationships",
        model=Entry,
    )
    comments = relations.HyperlinkedRelatedField(
        related_link_view_name="author-related",
        self_link_view_name="author-relationships",
        queryset=Comment.objects,
        many=True,
    )
    secrets = serializers.HiddenField(default="Shhhh!")
    defaults = serializers.CharField(
        default="default",
        max_length=20,
        min_length=3,
        write_only=True,
        help_text="help for defaults",
    )
    initials = serializers.SerializerMethodField()
    included_serializers = {
        "bio": AuthorBioSerializer,
        "author_type": AuthorTypeSerializer,
    }
    related_serializers = {
        "bio": "example.serializers.AuthorBioSerializer",
        "author_type": "example.serializers.AuthorTypeSerializer",
        "comments": "example.serializers.CommentSerializer",
        "entries": "example.serializers.EntrySerializer",
        "first_entry": "example.serializers.EntrySerializer",
    }

    class Meta:
        model = Author
        fields = (
            "name",
            "email",
            "bio",
            "entries",
            "comments",
            "first_entry",
            "author_type",
            "secrets",
            "defaults",
            "initials",
        )
        meta_fields = ("initials",)

    def get_first_entry(self, obj):
        return obj.entries.first()

    def get_initials(self, obj):
        return "".join([word[0] for word in obj.name.split(" ")])


class AuthorListSerializer(AuthorSerializer):
    pass


class AuthorDetailSerializer(AuthorSerializer):
    pass


class WriterSerializer(serializers.ModelSerializer):
    included_serializers = {"bio": AuthorBioSerializer}

    class Meta:
        model = Author
        fields = ("name", "email", "bio")
        resource_name = "writers"


class CommentSerializer(serializers.ModelSerializer):
    # testing remapping of related name
    writer = relations.ResourceRelatedField(source="author", read_only=True)
    modified_days_ago = serializers.SerializerMethodField()

    included_serializers = {
        "entry": EntrySerializer,
        "author": AuthorSerializer,
        "writer": WriterSerializer,
    }

    class Meta:
        model = Comment
        exclude = (
            "created_at",
            "modified_at",
        )
        # fields = ('entry', 'body', 'author',)
        meta_fields = ("modified_days_ago",)

    class JSONAPIMeta:
        included_resources = ("writer",)

    def get_modified_days_ago(self, obj):
        return (datetime.now() - obj.modified_at).days


class ProjectTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectType
        fields = (
            "name",
            "url",
        )


class BaseProjectSerializer(serializers.ModelSerializer):
    included_serializers = {
        "project_type": ProjectTypeSerializer,
    }


class ArtProjectSerializer(BaseProjectSerializer):
    class Meta:
        model = ArtProject
        exclude = ("polymorphic_ctype",)


class ResearchProjectSerializer(BaseProjectSerializer):
    # testing exclusive related field on inherited polymorphic model
    lab_results = relations.ResourceRelatedField(many=True, read_only=True)

    class Meta:
        model = ResearchProject
        exclude = ("polymorphic_ctype",)


class LabResultsSerializer(serializers.ModelSerializer):
    included_serializers = {"author": AuthorSerializer}

    class Meta:
        model = LabResults
        fields = ("date", "measurements", "author")


class ProjectSerializer(serializers.PolymorphicModelSerializer):
    included_serializers = {
        "project_type": ProjectTypeSerializer,
    }
    polymorphic_serializers = [ArtProjectSerializer, ResearchProjectSerializer]

    class Meta:
        model = Project
        exclude = ("polymorphic_ctype",)


class CurrentProjectRelatedField(relations.PolymorphicResourceRelatedField):
    def get_attribute(self, instance):
        obj = super().get_attribute(instance)

        is_art = self.field_name == "current_art_project" and isinstance(
            obj, ArtProject
        )
        is_res = self.field_name == "current_research_project" and isinstance(
            obj, ResearchProject
        )

        if is_art or is_res:
            return obj

        raise drf_fields.SkipField()


class CompanySerializer(serializers.ModelSerializer):
    current_project = relations.PolymorphicResourceRelatedField(
        ProjectSerializer, queryset=Project.objects.all()
    )
    current_art_project = CurrentProjectRelatedField(
        ProjectSerializer, source="current_project", read_only=True
    )
    current_research_project = CurrentProjectRelatedField(
        ProjectSerializer, source="current_project", read_only=True
    )
    future_projects = relations.PolymorphicResourceRelatedField(
        ProjectSerializer, queryset=Project.objects.all(), many=True
    )

    included_serializers = {
        "current_project": ProjectSerializer,
        "future_projects": ProjectSerializer,
        "current_art_project": ProjectSerializer,
        "current_research_project": ProjectSerializer,
    }

    class Meta:
        model = Company
        fields = "__all__"
