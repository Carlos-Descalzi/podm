# vim:ts=4:sw=4:expandtab
import unittest
from podm import JsonObject, Property, Handler, Processor, ArrayOf, MapOf
from collections import OrderedDict
from datetime import datetime
from .common import Entity, Company, Sector, Employee, DateTimeHandler, TestObject, TestObject2, Child, Parent


class TestSchema(unittest.TestCase):
    def test_json_schema(self):
        import json

        schema = Company.schema()
        self.assertIn("type", schema)
        self.assertIn("properties", schema)
        self.assertIn("py/object", schema["properties"])
        self.assertIn("const", schema["properties"]["py/object"])
        self.assertEqual("test.common.Company", schema["properties"]["py/object"]["const"])
        self.assertIn("oid", schema["properties"])
        self.assertIn("type", schema["properties"]["oid"])
        self.assertEqual("string", schema["properties"]["oid"]["type"])
        self.assertIn("created", schema["properties"])
        self.assertEqual("object", schema["properties"]["created"]["type"])
        self.assertIn("company-name", schema["properties"])
        self.assertEqual("string", schema["properties"]["company-name"]["type"])
        self.assertIn("description", schema["properties"])
        self.assertEqual("string", schema["properties"]["description"]["type"])
