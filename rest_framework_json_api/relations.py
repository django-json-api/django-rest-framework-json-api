from django.core.exceptions import ObjectDoesNotExist
from rest_framework.relations import HyperlinkedRelatedField


class JSONAPIRelatedField(HyperlinkedRelatedField):
    """
    This field exists for the sole purpose of accepting PKs as well as URLs
    when data is submitted back to the serializer
    """

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super(JSONAPIRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            super(JSONAPIRelatedField, self).to_internal_value(data)
        except AssertionError:
            if self.pk_field is not None:
                data = self.pk_field.to_internal_value(data)
            try:
                return self.get_queryset().get(pk=data)
            except ObjectDoesNotExist:
                self.fail('does_not_exist', pk_value=data)
            except (TypeError, ValueError):
                self.fail('incorrect_type', data_type=type(data).__name__)