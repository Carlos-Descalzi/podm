# vim:ts=4:sw=4:expandtab
__author__ = "Carlos Descalzi"

from abc import ABCMeta, abstractmethod
from enum import Enum, IntEnum
from .meta import Handler
from typing import Any, Type


class PropertyHandler(metaclass=ABCMeta):
    def handler(self) -> Handler:
        """
        Returns a custom handler for the property value, or None.
        """
        return None

    def field_type(self) -> Type:
        """
        Returns the type of the field value, intended when such value
        wants to be deserialized to a BaseJsonObject, and dictionary
        has no type information.
        """
        return None

    @abstractmethod
    def set(self, target: Any, value: Any):
        pass

    @abstractmethod
    def get(self, target: Any) -> Any:
        pass

    @abstractmethod
    def json(self) -> str:
        """
        Return the actual json name
        """
        pass

    @abstractmethod
    def field_name(self) -> str:
        """
        Return the field name.
        """
        pass


class RichPropertyHandler(PropertyHandler):
    """
    Adds features like default property value, enumerator handling and 
    better property accessor usage
    """

    @abstractmethod
    def init(self, target, value):
        """
        Initializes a property with a given value, or 
        a default value provided by this implementation.
        """
        pass

    @abstractmethod
    def enum_as_str(self) -> bool:
        """
        Boolean flag that determines if flags are stored/retrieved
        as string literals or integers.
        """
        pass

    @abstractmethod
    def getter(self):
        pass

    @abstractmethod
    def getter_name(self) -> str:
        pass

    @abstractmethod
    def setter(self):
        pass

    @abstractmethod
    def setter_name(self) -> str:
        pass


class DefaultSetter:
    def __init__(self, field_name):
        self._field_name = field_name

    def __call__(self, target, value):
        target.__dict__[self._field_name] = value


class DefaultGetter:
    def __init__(self, field_name):
        self._field_name = field_name

    def __call__(self, target):
        return target.__dict__[self._field_name]


class DefaultPropertyHandler(RichPropertyHandler):
    def __init__(self, obj_type, name, definition):
        self._name = name
        self._definition = definition
        self._field_name = "_%s" % name
        self._setter_name = "set_%s" % name
        self._getter_name = "get_%s" % name

        getter = obj_type.__dict__.get(self._getter_name)
        self._getter = getter or DefaultGetter(self._field_name)

        setter = obj_type.__dict__.get(self._setter_name)
        self._setter = setter or DefaultSetter(self._field_name)

    def init(self, target, value):
        self.set(target, value or self._definition.default_val())

    def set(self, target, value):
        self._setter(target, value)

    def get(self, target):
        return self._getter(target)

    def json(self):
        return self._definition.json or self._name

    def handler(self):
        return self._definition.handler

    def field_name(self):
        return self._field_name

    def field_type(self):
        return self._definition.type

    def enum_as_str(self):
        return self._definition.enum_as_str

    def getter(self):
        return self._getter

    def getter_name(self):
        return self._getter_name

    def setter(self):
        return self._setter

    def setter_name(self):
        return self._setter_name
