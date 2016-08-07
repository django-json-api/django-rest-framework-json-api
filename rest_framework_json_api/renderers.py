"""
Renderers
"""
import copy
from collections import OrderedDict, Iterable

from django.utils import six, encoding
from django.db.models.query import QuerySet

from rest_framework import relations
from rest_framework import renderers
from rest_framework.serializers import BaseSerializer, ListSerializer, ModelSerializer
from rest_framework.settings import api_settings
from rest_framework.fields import get_attribute

from . import utils


class JSONRenderer(renderers.JSONRenderer):
    """
    Render a JSON response per the JSON API spec:
    {
        "data": [{
            "type": "companies",
            "id": 1,
            "attributes": {
                "name": "Mozilla",
                "slug": "mozilla",
                "date-created": "2014-03-13 16:33:37"
            }
        }, {
            "type": "companies",
            "id": 2,
            ...
        }]
    }
    """

    media_type = 'application/vnd.api+json'
    format = 'vnd.api+json'

    @staticmethod
    def extract_attributes(fields, resource):
        data = OrderedDict()
        for field_name, field in six.iteritems(fields):
            # ID is always provided in the root of JSON API so remove it from attributes
            if field_name == 'id':
                continue
            # Skip fields with relations
            if isinstance(field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)):
                continue

            # Skip read_only attribute fields when `resource` is an empty
            # serializer. Prevents the "Raw Data" form of the browsable API
            # from rendering `"foo": null` for read only fields
            try:
                resource[field_name]
            except KeyError:
                if fields[field_name].read_only:
                    continue

            data.update({
                field_name: resource.get(field_name)
            })

        return utils.format_keys(data)

    @staticmethod
    def extract_relationships(fields, resource, resource_instance):
        # Avoid circular deps
        from rest_framework_json_api.relations import ResourceRelatedField

        data = OrderedDict()

        # Don't try to extract relationships from a non-existent resource
        if resource_instance is None:
            return

        for field_name, field in six.iteritems(fields):
            # Skip URL field
            if field_name == api_settings.URL_FIELD_NAME:
                continue

            # Skip fields without relations
            if not isinstance(field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)):
                continue

            source = field.source
            try:
                relation_instance_or_manager = get_attribute(resource_instance, source.split('.'))
            except AttributeError:
                # if the field is not defined on the model then we check the serializer
                # and if no value is there we skip over the field completely
                serializer_method = getattr(field.parent, source, None)
                if serializer_method and hasattr(serializer_method, '__call__'):
                    relation_instance_or_manager = serializer_method(resource_instance)
                else:
                    continue

            # relation_type = utils.get_related_resource_type(field)

            if isinstance(field, relations.HyperlinkedIdentityField):
                relation_type = utils.get_related_resource_type(field)
                # special case for HyperlinkedIdentityField
                relation_data = list()

                # Don't try to query an empty relation
                relation_queryset = relation_instance_or_manager.all() \
                    if relation_instance_or_manager is not None else list()

                for related_object in relation_queryset:
                    relation_data.append(
                            OrderedDict([('type', relation_type), ('id', encoding.force_text(related_object.pk))])
                    )

                data.update({field_name: {
                    'links': {
                        "related": resource.get(field_name)},
                    'data': relation_data,
                    'meta': {
                        'count': len(relation_data)
                    }
                }})
                continue

            if isinstance(field, ResourceRelatedField):
                # special case for ResourceRelatedField
                relation_data = {
                    'data': resource.get(field_name)
                }

                field_links = field.get_links(resource_instance)
                relation_data.update(
                        {'links': field_links}
                        if field_links else dict()
                )
                data.update({field_name: relation_data})
                continue

            if isinstance(field, (relations.PrimaryKeyRelatedField, relations.HyperlinkedRelatedField)):
                relation_id = relation_instance_or_manager.pk if resource.get(field_name) else None
                relation_type = utils.get_related_resource_type(field)

                relation_data = {
                    'data': (
                        OrderedDict([('type', relation_type), ('id', encoding.force_text(relation_id))])
                        if relation_id is not None else None)
                }

                relation_data.update(
                        {'links': {'related': resource.get(field_name)}}
                        if isinstance(field, relations.HyperlinkedRelatedField) and resource.get(field_name) else dict()
                )
                data.update({field_name: relation_data})
                continue

            if isinstance(field, relations.ManyRelatedField):

                if isinstance(field.child_relation, ResourceRelatedField):
                    # special case for ResourceRelatedField

                    if field_name not in resource:
                        continue


                    relation_data = {
                        'data': resource.get(field_name)
                    }

                    field_links = field.child_relation.get_links(resource_instance)
                    relation_data.update(
                            {'links': field_links}
                            if field_links else dict()
                    )
                    relation_data.update(
                            {
                                'meta': {
                                    'count': len(resource.get(field_name))
                                }
                            }
                    )
                    data.update({field_name: relation_data})
                    continue

                relation_data = list()
                for related_object in relation_instance_or_manager.all():
                    related_object_type = utils.get_instance_or_manager_resource_type(related_object)
                    relation_data.append(OrderedDict([
                        ('type', related_object_type),
                        ('id', encoding.force_text(related_object.pk))
                    ]))
                data.update({
                    field_name: {
                        'data': relation_data,
                        'meta': {
                            'count': len(relation_data)
                        }
                    }
                })
                continue

            if isinstance(field, ListSerializer):
                relation_data = list()

                serializer_data = resource.get(field_name)
                resource_instance_queryset = list(relation_instance_or_manager.all())
                if isinstance(serializer_data, list):
                    for position in range(len(serializer_data)):
                        nested_resource_instance = resource_instance_queryset[position]
                        nested_resource_instance_type = utils.get_resource_type_from_serializer(field.child)
                        relation_data.append(OrderedDict([
                            ('type', nested_resource_instance_type),
                            ('id', encoding.force_text(nested_resource_instance.pk))
                        ]))

                    data.update({field_name: {'data': relation_data}})
                    continue

            if isinstance(field, ModelSerializer):
                data.update({
                    field_name: {
                        'data': (
                            OrderedDict([
                                ('type', relation_type),
                                ('id', encoding.force_text(relation_instance_or_manager.pk))
                            ]) if resource.get(field_name) else None)
                    }
                })
                continue

        return utils.format_keys(data)

    @staticmethod
    def extract_included(fields, resource, resource_instance, included_resources):
        # this function may be called with an empty record (example: Browsable Interface)
        if not resource_instance:
            return

        included_data = list()
        current_serializer = fields.serializer
        context = current_serializer.context
        include_config = utils.get_included_configuration(current_serializer)
        included_resources = copy.copy(included_resources)

        for field_name, field in six.iteritems(fields):
            # Skip URL field
            if field_name == api_settings.URL_FIELD_NAME:
                continue

            # Skip fields without relations or serialized data
            if not isinstance(field, (relations.RelatedField, relations.ManyRelatedField, BaseSerializer)):
                continue

            # Skip disabled fields
            if include_config[field_name] == False:
                continue

            try:
                included_resources.remove(field_name)
            except ValueError:
                # Skip fields not in requested included resources
                continue

            try:
                relation_instance_or_manager = get_attribute(resource_instance, field.source.split('.'))
            except AttributeError:
                try:
                    # For ManyRelatedFields if `related_name` is not set we need to access `foo_set` from `source`
                    relation_instance_or_manager = get_attribute(resource_instance, field.child_relation.source.split('.'))
                except AttributeError:
                    if not hasattr(current_serializer, field.source):
                        continue
                    serializer_method = get_attribute(current_serializer, field.source.split('.'))
                    relation_instance_or_manager = serializer_method(resource_instance)

            new_included_resources = [key.replace('%s.' % field_name, '', 1)
                                      for key in included_resources
                                      if field_name == key.split('.')[0]]
            serializer_data = resource.get(field_name)

            serializer_instances = []

            if isinstance(field, relations.ManyRelatedField):
                # # serializer_class = include_config.get(field_name)
                # serializer_class = utils.get_serializer_from_instance_and_serializer()
                # serializer_instance = serializer_class(relation_instance_or_manager.all(), many=True, context=context)

                if isinstance(current_serializer.instance, Iterable):
                    iterable = []
                    for obj in current_serializer.instance:
                        iterable += field.get_attribute(obj)
                else:
                    iterable = field.get_attribute(current_serializer.instance)

                for item in iterable:
                    serializer_class = utils.get_serializer_from_instance_and_serializer(item,
                                                                                         current_serializer,
                                                                                         field_name)
                    serializer_instance = serializer_class(item, context=context)
                    serializer_instances.append(serializer_instance)

            if isinstance(field, relations.RelatedField):
                # serializer_class = include_config.get(field_name)
                if relation_instance_or_manager is None:
                    continue

                serializer_class = utils.get_serializer_from_instance_and_serializer(relation_instance_or_manager, current_serializer, field_name)
                serializer_instance = serializer_class(relation_instance_or_manager, context=context)
                serializer_instances.append(serializer_instance)

            for serializer_instance in serializer_instances:

                serializer_data = serializer_instance.data

                relation_type = utils.get_resource_type_from_serializer(serializer_instance.__class__)

                # Get the serializer fields
                serializer_fields = utils.get_serializer_fields(serializer_instance)
                if serializer_data:
                    included_data.append(
                            JSONRenderer.build_json_resource_obj(
                                    serializer_fields, serializer_data,
                                    serializer_instance.instance, relation_type)
                    )
                    included_data.extend(
                            JSONRenderer.extract_included(
                                    serializer_fields, serializer_data, serializer_instance.instance, new_included_resources
                            )
                    )

        return utils.format_keys(included_data)

    @staticmethod
    def extract_meta(serializer, resource):
        if hasattr(serializer, 'child'):
            meta = getattr(serializer.child, 'Meta', None)
        else:
            meta = getattr(serializer, 'Meta', None)
        meta_fields = getattr(meta, 'meta_fields', [])
        data = OrderedDict()
        for field_name in meta_fields:
            data.update({
                field_name: resource.get(field_name)
            })
        return data

    @staticmethod
    def extract_root_meta(serializer, resource, meta):
        if getattr(serializer, 'get_root_meta', None):
            root_meta = serializer.get_root_meta(resource)
            if root_meta:
                assert isinstance(root_meta, dict), 'get_root_meta must return a dict'
                meta.update(root_meta)
        return meta

    @staticmethod
    def build_json_resource_obj(fields, resource, resource_instance, resource_name):
        resource_data = [
            ('type', resource_name),
            ('id', encoding.force_text(resource_instance.pk) if resource_instance else None),
            ('attributes', JSONRenderer.extract_attributes(fields, resource)),
        ]
        relationships = JSONRenderer.extract_relationships(fields, resource, resource_instance)
        if relationships:
            resource_data.append(('relationships', relationships))
        # Add 'self' link if field is present and valid
        if api_settings.URL_FIELD_NAME in resource and \
                isinstance(fields[api_settings.URL_FIELD_NAME], relations.RelatedField):
            resource_data.append(('links', {'self': resource[api_settings.URL_FIELD_NAME]}))
        return OrderedDict(resource_data)

    def render_relationship_view(self, data, accepted_media_type=None, renderer_context=None):
        # Special case for RelationshipView
        view = renderer_context.get("view", None)
        render_data = OrderedDict([
            ('data', data)
        ])
        links = view.get_links()
        if links:
            render_data.update({'links': links}),
        return super(JSONRenderer, self).render(
                render_data, accepted_media_type, renderer_context
        )

    def render_errors(self, data, accepted_media_type=None, renderer_context=None):
        # Get the resource name.
        if len(data) > 1 and isinstance(data, list):
            data.sort(key=lambda x: x.get('source', {}).get('pointer', ''))
        return super(JSONRenderer, self).render(
                {'errors': data}, accepted_media_type, renderer_context
        )

    def render(self, data, accepted_media_type=None, renderer_context=None):

        view = renderer_context.get("view", None)
        request = renderer_context.get("request", None)

        from rest_framework_json_api.views import RelationshipView
        if isinstance(view, RelationshipView):
            return self.render_relationship_view(data, accepted_media_type, renderer_context)

        # Get the resource name.
        resource_name = utils.get_resource_name(renderer_context)

        # If `resource_name` is set to None then render default as the dev
        # wants to build the output format manually.
        if resource_name is None or resource_name is False:
            return super(JSONRenderer, self).render(
                    data, accepted_media_type, renderer_context
            )

        # If this is an error response, skip the rest.
        if resource_name == 'errors':
            return self.render_errors(data, accepted_media_type, renderer_context)

        include_resources_param = request.query_params.get('include') if request else None
        if include_resources_param:
            included_resources = include_resources_param.split(',')
        else:
            included_resources = list()

        json_api_included = list()
        # initialize json_api_meta with pagination meta or an empty dict
        json_api_meta = data.get('meta', {}) if isinstance(data, dict) else {}

        if data and 'results' in data:
            serializer_data = data["results"]
        else:
            serializer_data = data

        if hasattr(serializer_data, 'serializer') and getattr(serializer_data.serializer, 'many', False):
            # The below is not true for non-paginated responses
            # and isinstance(data, dict):

            # If detail view then json api spec expects dict, otherwise a list
            # - http://jsonapi.org/format/#document-top-level
            # The `results` key may be missing if unpaginated or an OPTIONS request

            resource_serializer = serializer_data.serializer

            # Get the serializer fields
            fields = utils.get_serializer_fields(resource_serializer)

            json_api_data = list()
            for position in range(len(serializer_data)):
                resource = serializer_data[position]  # Get current resource

                # If this is a queryset, ensure that the query is evaluated only once,
                # and do not assume the ordering of the serializer_data is in the same order,
                # since queries without an 'order_by' may not return in the same order.  Match
                # by pk instead.
                if isinstance(resource_serializer.instance, QuerySet):
                    id = resource['id']

                    # If 'id' field is sourced from another field, use the source field in the lookup
                    lookup_field = resource_serializer.child.fields['id'].source

                    resource_instance = filter(lambda item: getattr(item, lookup_field) == id,
                                               list(resource_serializer.instance))[0]
                else:
                    resource_instance = resource_serializer.instance[position]  # Get current instance

                json_resource_obj = self.build_json_resource_obj(fields, resource, resource_instance, resource_name)
                meta = self.extract_meta(resource_serializer, resource)
                if meta:
                    json_resource_obj.update({'meta': utils.format_keys(meta)})
                json_api_meta = self.extract_root_meta(resource_serializer, resource, json_api_meta)
                json_api_data.append(json_resource_obj)

                included = self.extract_included(fields, resource, resource_instance, included_resources)
                if included:
                    json_api_included.extend(included)
        else:
            # Check if data contains a serializer
            if hasattr(data, 'serializer'):
                fields = utils.get_serializer_fields(data.serializer)
                resource_instance = data.serializer.instance
                json_api_data = self.build_json_resource_obj(fields, data, resource_instance, resource_name)

                meta = self.extract_meta(data.serializer, data)
                if meta:
                    json_api_data.update({'meta': utils.format_keys(meta)})
                json_api_meta = self.extract_root_meta(data.serializer, data, json_api_meta)

                included = self.extract_included(fields, data, resource_instance, included_resources)
                if included:
                    json_api_included.extend(included)
            else:
                json_api_data = data

        # Make sure we render data in a specific order
        render_data = OrderedDict()

        if isinstance(data, dict) and data.get('links'):
            render_data['links'] = data.get('links')

        # format the api root link list
        if view.__class__ and view.__class__.__name__ == 'APIRoot':
            render_data['data'] = None
            render_data['links'] = json_api_data
        else:
            render_data['data'] = json_api_data

        if len(json_api_included) > 0:
            # Iterate through compound documents to remove duplicates
            seen = set()
            unique_compound_documents = list()
            for included_dict in json_api_included:
                type_tuple = tuple((included_dict['type'], included_dict['id']))
                if type_tuple not in seen:
                    seen.add(type_tuple)
                    unique_compound_documents.append(included_dict)

            # Sort the items by type then by id
            render_data['included'] = sorted(unique_compound_documents, key=lambda item: (item['type'], item['id']))

        if json_api_meta:
            render_data['meta'] = utils.format_keys(json_api_meta)

        return super(JSONRenderer, self).render(
                render_data, accepted_media_type, renderer_context
        )
