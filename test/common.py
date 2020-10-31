# vim:ts=4:sw=4:expandtab
import unittest
from podm import JsonObject, Property, Handler, Processor, ArrayOf, MapOf
from collections import OrderedDict
from datetime import datetime


class Entity(JsonObject):
    """
    A base class for the object model
    """

    oid = Property("oid", type=str)
    created = Property("created", default=datetime.now)


class Company(Entity):
    """
    This class represents a company.
    """

    company_name = Property("company-name", type=str)
    description = Property("description", type=str)

    def __init__(self, **kwargs):
        super(Company, self).__init__(**kwargs)
        # I use this field only for checking that the field "description"
        # is accessed from the getter instead of using default accessor.
        self._used_getter = False

    def get_description(self):
        # Set _used_getter to True if this getter has been called.
        self._used_getter = True
        return self._description


class Sector(Entity):
    employees = Property("employees", default=[])


class Employee(Entity):
    name = Property()


class DateTimeHandler(Handler):
    def encode(self, obj):
        return {
            "year": obj.year,
            "month": obj.month,
            "day": obj.day,
            "hour": obj.hour,
            "minute": obj.minute,
            "second": obj.second,
            "microsecond": obj.microsecond,
        }

    def decode(self, obj_data):
        return datetime(**obj_data)


class TestObject(JsonObject):

    date_time = Property("date-time", handler=DateTimeHandler(), default=datetime.now)

    def __init__(self, **kwargs):
        JsonObject.__init__(self, **kwargs)
        self._deserialized = False

    def _after_deserialize(self):
        self._deserialized = True


class TestObject2(JsonObject):
    property1 = Property()


class Child(JsonObject):
    property1 = Property()


class Parent(JsonObject):
    children = Property(type=ArrayOf(Child))
