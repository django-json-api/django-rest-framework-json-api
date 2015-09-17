from rest_framework.exceptions import ValidationError
from rest_framework.relations import *


class HyperlinkedRelatedField(HyperlinkedRelatedField):
    """
    This field exists for the sole purpose of accepting PKs as well as URLs
    when data is submitted back to the serializer
    """

    def __init__(self, **kwargs):
        self.pk_field = kwargs.pop('pk_field', None)
        super(HyperlinkedRelatedField, self).__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            # Try parsing links first for the browseable API
            return super(HyperlinkedRelatedField, self).to_internal_value(data)
        except ValidationError:
            if self.pk_field is not None:
                data = self.pk_field.to_internal_value(data)
            try:
                return self.get_queryset().get(pk=data)
            except ObjectDoesNotExist:
                self.fail('does_not_exist', pk_value=data)
            except (TypeError, ValueError):
                self.fail('incorrect_type', data_type=type(data).__name__)