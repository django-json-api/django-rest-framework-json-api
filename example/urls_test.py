from django.urls import re_path
from rest_framework import routers

from .api.resources.identity import GenericIdentity, Identity
from example.views import (
    AuthorRelationshipView,
    AuthorViewSet,
    BlogRelationshipView,
    BlogViewSet,
    CommentRelationshipView,
    CommentViewSet,
    CompanyViewset,
    DRFBlogViewSet,
    DRFEntryViewSet,
    EntryRelationshipView,
    EntryViewSet,
    FiltersetEntryViewSet,
    LabResultViewSet,
    NoFiltersetEntryViewSet,
    NonPaginatedEntryViewSet,
    ProjectTypeViewset,
    ProjectViewset,
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(r"blogs", BlogViewSet)
# router to test default DRF blog functionalities
router.register(r"drf-blogs", DRFBlogViewSet, "drf-entry-blog")
router.register(r"entries", EntryViewSet)
# these "flavors" of entries are used for various tests:
router.register(r"nopage-entries", NonPaginatedEntryViewSet, "nopage-entry")
router.register(r"filterset-entries", FiltersetEntryViewSet, "filterset-entry")
router.register(r"nofilterset-entries", NoFiltersetEntryViewSet, "nofilterset-entry")
router.register(r"authors", AuthorViewSet)
router.register(r"comments", CommentViewSet)
router.register(r"companies", CompanyViewset)
router.register(r"projects", ProjectViewset)
router.register(r"project-types", ProjectTypeViewset)
router.register(r"lab-results", LabResultViewSet)

# for the old tests
router.register(r"identities", Identity)

urlpatterns = [
    # old tests
    re_path(
        r"identities/default/(?P<pk>\d+)$",
        GenericIdentity.as_view(),
        name="user-default",
    ),
    re_path(
        r"^entries/(?P<entry_pk>[^/.]+)/blog$",
        BlogViewSet.as_view({"get": "retrieve"}),
        name="entry-blog",
    ),
    re_path(
        r"^entries/(?P<entry_pk>[^/.]+)/comments$",
        CommentViewSet.as_view({"get": "list"}),
        name="entry-comments",
    ),
    re_path(
        r"^entries/(?P<entry_pk>[^/.]+)/suggested/$",
        EntryViewSet.as_view({"get": "list"}),
        name="entry-suggested",
    ),
    re_path(
        r"^drf-entries/(?P<entry_pk>[^/.]+)/suggested/$",
        DRFEntryViewSet.as_view({"get": "list"}),
        name="drf-entry-suggested",
    ),
    re_path(
        r"entries/(?P<entry_pk>[^/.]+)/authors$",
        AuthorViewSet.as_view({"get": "list"}),
        name="entry-authors",
    ),
    re_path(
        r"entries/(?P<entry_pk>[^/.]+)/featured$",
        EntryViewSet.as_view({"get": "retrieve"}),
        name="entry-featured",
    ),
    re_path(
        r"^authors/(?P<pk>[^/.]+)/(?P<related_field>[-\w]+)/$",
        AuthorViewSet.as_view({"get": "retrieve_related"}),
        name="author-related",
    ),
    re_path(
        r"^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>[\-\w]+)$",
        EntryRelationshipView.as_view(),
        name="entry-relationships",
    ),
    re_path(
        r"^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>[^/.]+)$",
        BlogRelationshipView.as_view(),
        name="blog-relationships",
    ),
    re_path(
        r"^comments/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        CommentRelationshipView.as_view(),
        name="comment-relationships",
    ),
    re_path(
        r"^authors/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$",
        AuthorRelationshipView.as_view(),
        name="author-relationships",
    ),
]

urlpatterns += router.urls
