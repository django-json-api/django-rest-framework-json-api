
# API

## mixins
### MultipleIDMixin

Add this mixin to a view to override `get_queryset` to automatically filter
records by `ids[]=1&ids[]=2` in URL query params.

