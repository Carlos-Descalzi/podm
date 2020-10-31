# vim:ts=4:sw=4:expandtab
__author__ = "Carlos Descalzi"

from abc import ABCMeta, abstractmethod
from typing import Any, Mapping, Type
import copy


class Handler(metaclass=ABCMeta):
    """
    Interface for custom serialization handlers
    """

    @abstractmethod
    def encode(self, value: Any) -> Any:
        """
        Returns a json-friendly representation of the given value
        """
        return value

    @abstractmethod
    def decode(self, value_dict: Any) -> Any:
        """
        Converts back the dictionary into a desired type.
        """
        return value_dict


class CollectionOf:
    def __init__(self, type: Type):
        self._type = type

    @property
    def type(self) -> Type:
        return self._type


class ArrayOf(CollectionOf):
    """
    Describe an array of a given type.
    """

    pass


class MapOf(CollectionOf):
    """
    Describe a map a given value type.
    """

    pass


class Property(object):
    """
    Defines a property for a JSON object
    It allows to customize the json field name and the type
    used to deserialize the object.
    """

    def __init__(
        self,
        json=None,
        type=None,
        default=None,
        handler=None,
        enum_as_str=False,
        allow_none=True,
        validator=None,
        title=None,
        description=None,
    ):
        """
        Parameters:
        json: The json field name, can be different from the field name.
        type: The value type, useful when serializing data with no type information
        default: The default value when an object is instantiated. If it is a function/lambda
            it will invoke it to get a new value, otherwise this value is copied for each instance
        handler: Custom serialization handler for the value contained in the property 
        enum_as_str: Handle enumerators as strings.
        allow_none: Allows None as value.
        validator: Allow specify a validator for this property. Possible values are, None for no validation, 
            an implementation of Validator interface, or "default" to use default validation.
        """
        self._json = json
        self._type = type
        self._default = default
        self._handler = handler
        self._enum_as_str = enum_as_str
        self._allow_none = allow_none
        self._validator = validator
        self._title = title
        self._description = description

    @property
    def json(self) -> str:
        """
        JSON Field name, by default is the name of the attribute
        """
        return self._json

    @property
    def type(self):
        """
        Vault type, only required when value is instance of JsonObject
        """
        return self._type

    @property
    def default(self) -> Any:
        """
        Default value when object is instantiated.
        If it is a callable, it will be called to get the new value,
        otherwise this value will be used as prototype and copied on each instance.
        """
        return self._default

    @property
    def handler(self) -> Handler:
        """
        Custom handler for serializing/deserializing this field value.
        """
        return self._handler

    @property
    def enum_as_str(self) -> bool:
        """
        Determines if enums must be handled as string or int
        """
        return self._enum_as_str

    @property
    def validator(self):
        return self._validator

    @property
    def allow_none(self):
        return self._allow_none

    def default_val(self) -> Any:
        """
        Returns a new instance of the default vault for this field.
        """
        default = self.default
        if callable(default):
            return default()
        elif default is not None:
            return copy.deepcopy(default)
        return None

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description
