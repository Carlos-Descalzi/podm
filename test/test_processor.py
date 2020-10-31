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


class TestProcessor(unittest.TestCase):
    def test_processor(self):
        class UpperCaseProcessor(Processor):
            def when_from_dict(self, key, val):
                return key.lower(), val

            def when_to_dict(self, key, val):
                return key.upper(), val

        class TestObject(JsonObject):
            property1 = Property()

        test_object = TestObject()
        test_object.property1 = "hello!!"

        serialized = test_object.to_dict(processor=UpperCaseProcessor())
        self.assertIn("PROPERTY1", serialized)

        deserialized = TestObject.from_dict(serialized, processor=UpperCaseProcessor())
        self.assertEqual("hello!!", deserialized.property1)


if __name__ == "__main__":
    unittest.main()
