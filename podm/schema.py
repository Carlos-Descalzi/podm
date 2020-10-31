from collections import OrderedDict
from enum import Enum


class SchemaBuilder:
    def __init__(self, obj_type):
        self._obj_type = obj_type

    def build(self):

        obj_properties = self._obj_type.properties()

        definitions = self._collect_definitions(obj_properties)

        properties = OrderedDict(
            [(p.json(), p.schema(definitions)) for p in obj_properties.values()]
        )

        schema = OrderedDict(
            [
                ("type", "object"),
                (
                    "properties",
                    OrderedDict(
                        [("py/object", {"const": self._obj_type.object_type_name()})]
                    ),
                ),
            ]
        )
        if self._obj_type.__jsonpickle_format__:
            schema["properties"]["py/state"] = {"$ref": "#/definitions/state"}
            definitions.update(
                {"state": OrderedDict([("type", "object"), ("properties", properties)])}
            )
        else:
            schema["properties"].update(properties)

        if definitions:
            schema["definitions"] = definitions

        return schema

    def _collect_definitions(self, properties):

        result = {}
        for prop in properties.values():
            field_type = prop.field_type()
            if (
                field_type
                and not self._primitive(field_type)
                and issubclass(field_type, object)
                and not issubclass(field_type, Enum)
            ):
                result[field_type.__name__] = field_type.schema()

        return result

    def _primitive(self, type):
        return type in [int, bool, float, str]
