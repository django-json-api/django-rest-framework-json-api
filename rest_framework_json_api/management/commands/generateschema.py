from rest_framework.management.commands.generateschema import Command as DRFCommand

from rest_framework_json_api.schemas.openapi import SchemaGenerator


class Command(DRFCommand):
    help = "Generates jsonapi.org schema for project."

    def get_generator_class(self):
        return SchemaGenerator
