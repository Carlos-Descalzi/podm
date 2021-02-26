from unittest import TestCase
from podm import JsonObject, Property


class TestObject(JsonObject):
    field1 = Property(default=1)
    field2 = Property(default=True)
    field3 = Property(default=False)
    field4 = Property(default=dict)
    field5 = Property(default=lambda: [1, 2, 3])


class TestDefaults(TestCase):
    def test_default_int(self):
        obj = TestObject()
        self.assertEqual(1, obj.field1)

    def test_default_bool_true(self):
        obj = TestObject()
        self.assertTrue(obj.field2)

    def test_default_bool_false(self):
        obj = TestObject()
        self.assertFalse(obj.field3)

    def test_default_dict(self):
        obj = TestObject()
        self.assertEqual({}, obj.field4)

    def test_default_list_factory(self):
        obj = TestObject()
        self.assertEqual([1, 2, 3], obj.field5)

    def test_constructors(self):
        obj = TestObject(field1=2, field2=False, field3=True, field4={"a": 1}, field5=[4, 5, 6])
        self.assertEqual(2, obj.field1)
        self.assertFalse(obj.field2)
        self.assertTrue(obj.field3)
        self.assertEqual({"a": 1}, obj.field4)
        self.assertEqual([4, 5, 6], obj.field5)
