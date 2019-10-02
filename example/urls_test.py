from django.conf.urls import include, url
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
    NoFiltersetEntryViewSet,
    NonPaginatedEntryViewSet,
    ProjectTypeViewset,
    ProjectViewset
)

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'blogs', BlogViewSet)
# router to test default DRF blog functionalities
router.register(r'drf-blogs', DRFBlogViewSet, 'drf-entry-blog')
router.register(r'entries', EntryViewSet)
# these "flavors" of entries are used for various tests:
router.register(r'nopage-entries', NonPaginatedEntryViewSet, 'nopage-entry')
router.register(r'filterset-entries', FiltersetEntryViewSet, 'filterset-entry')
router.register(r'nofilterset-entries', NoFiltersetEntryViewSet, 'nofilterset-entry')
router.register(r'authors', AuthorViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'companies', CompanyViewset)
router.register(r'projects', ProjectViewset)
router.register(r'project-types', ProjectTypeViewset)

# for the old tests
router.register(r'identities', Identity)

urlpatterns = [
    url(r'^', include(router.urls)),

    # old tests
    url(r'identities/default/(?P<pk>\d+)$',
        GenericIdentity.as_view(), name='user-default'),


    url(r'^entries/(?P<entry_pk>[^/.]+)/blog$',
        BlogViewSet.as_view({'get': 'retrieve'}),
        name='entry-blog'
        ),
    url(r'^entries/(?P<entry_pk>[^/.]+)/comments$',
        CommentViewSet.as_view({'get': 'list'}),
        name='entry-comments'
        ),
    url(r'^entries/(?P<entry_pk>[^/.]+)/suggested/$',
        EntryViewSet.as_view({'get': 'list'}),
        name='entry-suggested'
        ),
    url(r'^drf-entries/(?P<entry_pk>[^/.]+)/suggested/$',
        DRFEntryViewSet.as_view({'get': 'list'}),
        name='drf-entry-suggested'
        ),
    url(r'entries/(?P<entry_pk>[^/.]+)/authors$',
        AuthorViewSet.as_view({'get': 'list'}),
        name='entry-authors'),
    url(r'entries/(?P<entry_pk>[^/.]+)/featured$',
        EntryViewSet.as_view({'get': 'retrieve'}),
        name='entry-featured'),

    url(r'^authors/(?P<pk>[^/.]+)/(?P<related_field>\w+)/$',
        AuthorViewSet.as_view({'get': 'retrieve_related'}),
        name='author-related'),

    url(r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$',
        EntryRelationshipView.as_view(),
        name='entry-relationships'),
    url(r'^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$',
        BlogRelationshipView.as_view(),
        name='blog-relationships'),
    url(r'^comments/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$',
        CommentRelationshipView.as_view(),
        name='comment-relationships'),
    url(r'^authors/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)$',
        AuthorRelationshipView.as_view(),
        name='author-relationships'),
]
