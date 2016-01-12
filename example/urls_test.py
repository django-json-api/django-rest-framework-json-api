from django.conf.urls import include, url
from rest_framework import routers

from example.views import BlogViewSet, EntryViewSet, AuthorViewSet, CommentViewSet, EntryRelationshipView, BlogRelationshipView, \
    CommentRelationshipView, AuthorRelationshipView
from .api.resources.identity import Identity, GenericIdentity

router = routers.DefaultRouter(trailing_slash=False)

router.register(r'blogs', BlogViewSet)
router.register(r'entries', EntryViewSet)
router.register(r'authors', AuthorViewSet)
router.register(r'comments', CommentViewSet)

# for the old tests
router.register(r'identities', Identity)

urlpatterns = [
    url(r'^', include(router.urls)),

    # old tests
    url(r'identities/default/(?P<pk>\d+)',
        GenericIdentity.as_view(), name='user-default'),


    url(r'^entries/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        EntryRelationshipView.as_view(),
        name='entry-relationships'),
    url(r'^blogs/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        BlogRelationshipView.as_view(),
        name='blog-relationships'),
    url(r'^comments/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        CommentRelationshipView.as_view(),
        name='comment-relationships'),
    url(r'^authors/(?P<pk>[^/.]+)/relationships/(?P<related_field>\w+)',
        AuthorRelationshipView.as_view(),
        name='author-relationships'),
]

