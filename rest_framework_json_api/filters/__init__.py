import pkgutil
from .sort import JSONAPIOrderingFilter  # noqa: F401
# If django-filter is not installed, no-op.
if pkgutil.find_loader('django_filters') is not None:
    from .django_filter import DjangoFilterBackend  # noqa: F401
del pkgutil
