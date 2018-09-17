import re

from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend


class QueryValidationFilter(BaseFilterBackend):
    """
    A backend filter that performs strict validation of query parameters for
    jsonapi spec conformance and raises a 400 error if non-conforming usage is
    found.

    If you want to add some additional non-standard query parameters,
    simply override `.query_regex` adding the new parameters but, "with the additional
    requirement that they MUST contain contain at least one non a-z character (U+0061 to U+007A).
    It is RECOMMENDED that a U+002D HYPHEN-MINUS, "-", U+005F LOW LINE, "_", or capital letter is
    used (e.g. camelCasing)."  -- http://jsonapi.org/format/#query-parameters
    """
    #: compiled regex that matches the allowed http://jsonapi.org/format/#query-parameters
    #: `sort` and `include` stand alone; `filter`, `fields`, and `page` have []'s
    query_regex = re.compile(r'^(sort|include)$|^(filter|fields|page)(\[[\w\.\-]+\])?$')

    def validate_query_params(self, request):
        """
        Validate that query params are in the list of valid query keywords
        Raises ValidationError if not.
        """
        # TODO: For jsonapi error object conformance, must set jsonapi errors "parameter" for
        # the ValidationError. This requires extending DRF/DJA Exceptions.
        for qp in request.query_params.keys():
            if not self.query_regex.match(qp):
                raise ValidationError('invalid query parameter: {}'.format(qp))
            if len(request.query_params.getlist(qp)) > 1:
                raise ValidationError(
                    'repeated query parameter not allowed: {}'.format(qp))

    def filter_queryset(self, request, queryset, view):
        self.validate_query_params(request)
        return queryset
