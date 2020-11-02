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


class TestSerialization(unittest.TestCase):
    def test_properties(self):
        self.assertEqual(set(Entity.property_names()), set(["oid", "created"]))
        self.assertEqual(
            set(Company.property_names()), set(["oid", "created", "description", "company_name"]),
        )
        self.assertEqual(
            set(Company.json_field_names()), set(["oid", "created", "description", "company-name"]),
        )

    def test_accessors(self):
        company = Company()
        company.oid = "123123123"
        company.company_name = "master"
        company.description = "master company"

        self.assertEqual("master", company.company_name)

        self.assertEqual("master", company.get_company_name())
        self.assertEqual("master company", company.description)
        self.assertTrue(company._used_getter)
        company._used_getter = False
        self.assertEqual("master company", company.get_description())
        self.assertTrue(company._used_getter)

        company.set_description("desc 2")
        self.assertEqual("desc 2", company.description)
        self.assertEqual("desc 2", company._description)

    def test_to_dict(self):
        company = Company()
        company.company_name = "master"
        company.description = "master company"

        data = company.to_dict()

        self.assertTrue("py/object" in data)
        print(data["py/object"])
        self.assertTrue("oid" in data)
        self.assertTrue("created" in data)
        self.assertIsNotNone(data["created"])
        self.assertTrue("company-name" in data)
        self.assertEqual("master", data["company-name"])
        self.assertTrue("description" in data)
        self.assertEqual("master company", data["description"])

    def test_deserialize_no_module(self):
        data = {
            "py/object": "Company",
            "py/state": {"company-name": "master", "description": "some description"},
        }
        company = JsonObject.parse(data, __name__)
        self.assertTrue(isinstance(company, Company))
        self.assertEqual("master", company.company_name)
        self.assertEqual("some description", company.description)

    def test_deserialize_with_module(self):
        data = {
            "py/object": "test.common.Company",
            "py/state": {"company-name": "master", "description": "some description"},
        }
        company = JsonObject.parse(data)
        self.assertTrue(isinstance(company, Company))
        self.assertEqual("master", company.company_name)
        self.assertEqual("some description", company.description)

    def test_deserialize_3(self):
        data = {"company-name": "master", "description": "some description"}
        company = Company.from_dict(data)
        self.assertTrue(isinstance(company, Company))
        self.assertEqual("master", company.company_name)
        self.assertEqual("some description", company.description)

    def test_kwargs_constructor(self):
        company = Company(company_name="master", description="some description")

        # check accessors
        self.assertEqual("master", company.company_name)
        self.assertEqual("some description", company.description)

        # check internal state
        self.assertEqual("master", company._company_name)
        self.assertEqual("some description", company._description)

    def test_collections(self):
        sector = Sector()
        employee = Employee(oid="1234", name="xx1")

        sector.employees.append(employee)

        data = sector.to_dict()

        self.assertTrue(isinstance(data["employees"], list))

        for employee in data["employees"]:
            self.assertEqual("1234", employee["oid"])
            self.assertEqual("xx1", employee["name"])

        new_sector = Sector.from_dict(data)

        self.assertTrue(isinstance(new_sector.employees, list))
        self.assertEqual(1, len(new_sector.employees))

        self.assertTrue(isinstance(new_sector.employees[0], Employee))
        self.assertEqual("1234", new_sector.employees[0].oid)
        self.assertEqual("xx1", new_sector.employees[0].name)

    def test_default(self):
        k1 = Company()
        k2 = Company()

        self.assertIsNotNone(k1.created)
        self.assertIsNotNone(k2.created)

        self.assertNotEqual(k1.created, k2.created)

    def test_custom_objects(self):

        company = Company(created=datetime.now())

        company_dict = company.to_dict()

        self.assertTrue("created" in company_dict)
        self.assertTrue(isinstance(company_dict["created"], datetime))

    def test_handler(self):

        obj = TestObject()

        obj_dict = obj.to_dict()
        self.assertTrue(isinstance(obj_dict["date-time"], dict))
        self.assertTrue("year" in obj_dict["date-time"])

        obj2 = TestObject.from_dict(obj_dict)
        self.assertTrue(isinstance(obj2.date_time, datetime))

        self.assertTrue(obj2._deserialized)

    def test_handler_2(self):
        class BoolHandler(Handler):
            def encode(self, val):
                return val

            def decode(self, val):
                print("decode", val)
                return str(val).lower() == "true" if val is not None else None

        bool_handler = BoolHandler()

        class TestObject2(JsonObject):
            some_boolean_1 = Property(handler=bool_handler)
            some_boolean_2 = Property(handler=bool_handler)
            some_boolean_3 = Property(handler=bool_handler)

        obj_dict = {
            "some_boolean_1": "True",
            "some_boolean_2": "false",
            "some_boolean_3": None,
        }

        obj = TestObject2.from_dict(obj_dict)

        self.assertIsInstance(obj.some_boolean_1, bool)
        self.assertTrue(isinstance(obj.some_boolean_2, bool))
        self.assertIsNone(obj.some_boolean_3)

    def test_str(self):
        class TestObject3(JsonObject):
            val1 = Property()
            val2 = Property()
            val3 = Property()

        obj_dict = {"val1": "Hi", "val2": True, "val3": None}

        obj = TestObject3.from_dict(obj_dict)

        obj_str = str(obj)

        self.assertEqual("TestObject3:val1=Hi;val2=True;val3=None", obj_str)

    def test_ordered_dict(self):
        class TestObject4(JsonObject):
            val1 = Property()

        obj = TestObject4()
        obj.val1 = OrderedDict(key1="value1", key2="value2", key3="value3", key4="value4")

        serialized = obj.to_dict(OrderedDict)
        self.assertTrue(isinstance(serialized, OrderedDict))
        self.assertTrue(isinstance(serialized["val1"], OrderedDict))

        serialized = obj.to_dict()
        self.assertFalse(isinstance(serialized, OrderedDict))
        self.assertTrue(isinstance(serialized["val1"], OrderedDict))

    def test_yaml(self):
        class TestObject4(JsonObject):
            val1 = Property()
            val2 = Property()

        obj = TestObject4()
        obj.val1 = {"key1": "val1"}
        obj.val2 = [1, 2, 3]
        import yaml

        print()
        print(yaml.dump(obj.to_dict()))

    def test_enums_str(self):
        from enum import Enum, auto

        class Enum1(Enum):
            VAL1 = 1
            VAL2 = 2

        class TestObject(JsonObject):
            val = Property(type=Enum1, enum_as_str=True)

        obj = TestObject()
        obj.val = Enum1.VAL1

        data = obj.to_dict()
        self.assertEqual("VAL1", data["val"])

        obj2 = TestObject.from_dict(data)
        self.assertEqual(Enum1.VAL1, obj2.val)

    def test_enums_int(self):
        from enum import Enum, auto

        class Enum1(Enum):
            VAL1 = 1
            VAL2 = 2

        class TestObject(JsonObject):
            val = Property(type=Enum1)

        obj = TestObject()
        obj.val = Enum1.VAL1

        data = obj.to_dict()
        self.assertEqual(1, data["val"])

        obj2 = TestObject.from_dict(data)
        self.assertEqual(Enum1.VAL1, obj2.val)

    def test_int_enums_int(self):
        from enum import IntEnum, auto

        class Enum1(IntEnum):
            VAL1 = 1
            VAL2 = 2

        class TestObject(JsonObject):
            val = Property(type=Enum1)

        obj = TestObject()
        obj.val = Enum1.VAL1

        data = obj.to_dict()
        self.assertEqual(1, data["val"])
        self.assertFalse(isinstance(data["val"], IntEnum))

        obj2 = TestObject.from_dict(data)
        self.assertEqual(Enum1.VAL1, obj2.val)

    def test_plain_props(self):
        class TestObject(JsonObject):
            prop1 = Property()

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self._prop2 = None

            def set_prop2(self, prop2):
                self._prop2 = prop2

            def get_prop2(self):
                return self._prop2

            prop2 = property(get_prop2, set_prop2)

        obj = TestObject()

        self.assertIsNone(obj.prop2)
        try:
            obj.prop2 = 1
        except AttributeError:
            self.assertTrue(False)

        val = obj.prop2

        self.assertEqual(1, val)

    def test_jsonpickle_format(self):
        class TestObject(JsonObject):

            __jsonpickle_format__ = True

            prop1 = Property()

        obj = TestObject()
        obj.prop1 = "hello"

        data = obj.to_dict()

        self.assertIn("py/object", data)
        self.assertIn("py/state", data)

        self.assertIn("prop1", data["py/state"])
        self.assertEqual("hello", data["py/state"]["prop1"])

    def test_nested(self):

        test_obj = TestObject2()
        test_obj.property1 = "hello"

        data = {"obj": test_obj.to_dict()}

        parsed = JsonObject.parse(data)

        self.assertIsInstance(parsed, dict)
        self.assertIn("obj", parsed)
        self.assertIsInstance(parsed["obj"], TestObject2)

    def test_explicity_typing_in_array(self):

        data = {"children": [{"property1": "value1"}]}

        obj = Parent.from_dict(data)

        self.assertIsNotNone(obj)
        self.assertEqual(1, len(obj.children))
        self.assertIsInstance(obj.children[0], Child)


if __name__ == "__main__":
    unittest.main()
