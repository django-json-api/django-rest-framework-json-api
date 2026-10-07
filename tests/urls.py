from rest_framework.routers import SimpleRouter

from tests.views import (
    BasicModelViewSet,
    ForeignKeySourcetHyperlinkedViewSet,
    ForeignKeySourceViewSet,
    ForeignKeyTargetViewSet,
    ManyToManySourceViewSet,
    NestedRelatedSourceViewSet,
    URLModelViewSet,
)

router = SimpleRouter()
router.register(r"basic_models", BasicModelViewSet)
router.register(r"url_models", URLModelViewSet)
router.register(r"foreign_key_sources", ForeignKeySourceViewSet)
router.register(r"foreign_key_targets", ForeignKeyTargetViewSet)
router.register(
    r"foreign_key_sources_hyperlinked",
    ForeignKeySourcetHyperlinkedViewSet,
    "foreignkeysourcehyperlinked",
)
router.register(
    r"many_to_many_sources", ManyToManySourceViewSet, basename="many-to-many-source"
)
router.register(
    r"nested_related_sources",
    NestedRelatedSourceViewSet,
    basename="nested-related-source",
)
urlpatterns = router.urls
