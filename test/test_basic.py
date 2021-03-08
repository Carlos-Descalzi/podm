from podm import JsonObject, Property
from unittest import TestCase


class TestObject1(JsonObject):
    field1 = Property()

    def get_field2(self):
        return self._field2

    def set_field2(self, field2):
        self._field2 = field2

    field2 = property(get_field2, set_field2)

    def update_field2(self, val):
        self.field2 = val


class TestObject2(TestObject1):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._field2 = None


class TestBasic(TestCase):
    def test_mixed_properties(self):
        """
        Test for a bug when a regular property is in a base class,
        subclasses not being able to see it.
        """
        obj = TestObject2()
        obj.field2 = 1
        self.assertEqual(1, obj.field2)
        self.assertEqual(1, obj.get_field2())
        obj.update_field2(2)
        self.assertEqual(2, obj.field2)
