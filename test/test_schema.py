# vim:ts=4:sw=4:expandtab
import unittest
from podm import JsonObject, Property, Handler, Processor, ArrayOf, MapOf
from collections import OrderedDict
from datetime import datetime
from .common import (
    Entity,
    Company,
    Sector,
    Employee,
    DateTimeHandler,
    TestObject,
    TestObject2,
    Child,
    Parent,
)
from enum import Enum


class Values(Enum):
    VALUE1 = 1
    VALUE2 = 2


class Type2(JsonObject):
    field_1 = Property(type=int, title="Field 1 title")
    field_2 = Property(type=Values, enum_as_str=True)


class Type1(JsonObject):

    field_1 = Property(type=str)
    field_2 = Property(type=Type2)


class TestSchema(unittest.TestCase):
    def test_base_schema(self):
        schema = Company.schema()
        self.assertIn("type", schema)
        self.assertIn("properties", schema)
        self.assertIn("py/object", schema["properties"])
        self.assertIn("const", schema["properties"]["py/object"])
        self.assertEqual(
            "test.common.Company", schema["properties"]["py/object"]["const"]
        )
        self.assertIn("oid", schema["properties"])
        self.assertIn("type", schema["properties"]["oid"])
        self.assertEqual("string", schema["properties"]["oid"]["type"])
        self.assertIn("created", schema["properties"])
        self.assertEqual("object", schema["properties"]["created"]["type"])
        self.assertIn("company-name", schema["properties"])
        self.assertEqual("string", schema["properties"]["company-name"]["type"])
        self.assertIn("description", schema["properties"])
        self.assertEqual("string", schema["properties"]["description"]["type"])

    def test_compound(self):
        import json

        schema = Type1.schema()
        print(json.dumps(schema, indent=4))
        self.assertEqual(schema["type"], "object")
        self.assertEqual(
            schema["properties"]["field_2"]["type"], {"$ref": "#/definitions/Type2"}
        )
        self.assertEqual(1, len(schema["definitions"]))
        self.assertIn("properties", schema["definitions"]["Type2"])
        self.assertIn("field_1", schema["definitions"]["Type2"]["properties"])
        self.assertIn("title", schema["definitions"]["Type2"]["properties"]["field_1"])
        self.assertIn("field_2", schema["definitions"]["Type2"]["properties"])
        self.assertIn("enum", schema["definitions"]["Type2"]["properties"]["field_2"])
        self.assertEqual(
            set(["VALUE1", "VALUE2"]),
            set(schema["definitions"]["Type2"]["properties"]["field_2"]["enum"]),
        )
