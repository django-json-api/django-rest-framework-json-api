import re

from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend


class QueryParameterValidationFilter(BaseFilterBackend):
    """
    A backend filter that performs strict validation of query parameters for
    jsonapi spec conformance and raises a 400 error if non-conforming usage is
    found.

    If you want to add some additional non-standard query parameters,
    override :py:attr:`query_regex` adding the new parameters. Make sure to comply with
    the rules at http://jsonapi.org/format/#query-parameters.
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
