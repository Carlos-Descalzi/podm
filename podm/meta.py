__author__ = 'Carlos Descalzi'

from abc import ABCMeta, abstractmethod
import copy

class Handler(metaclass=ABCMeta):
    """
    Interface for custom serialization handlers
    """
    @abstractmethod
    def encode(self, value):
        """
        Returns a json-friendly representation of the given value
        """
        return value

    @abstractmethod
    def decode(self, value_dict):
        """
        Converts back the dictionary into a desired type.
        """
        return value_dict

class Property(object):
    """
    Defines a property for a JSON object
    It allows to customize the json field name and the type
    used to deserialize the object.
    """
    def __init__(self, json=None, type=None, default=None, handler=None, enum_as_str=False):
        """
        Parameters:
        json: The json field name, can be different from the field name.
        type: The value type, useful when serializing data with no type information
        default: The default value when an object is instantiated. If it is a function/lambda
            it will invoke it to get a new value, otherwise this value is copied for each instance
        handler: Custom serialization handler for the value contained in the property 
        """
        self._json = json
        self._type = type
        self._default = default
        self._handler = handler
        self._enum_as_str = enum_as_str

    @property
    def json(self):
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
    def default(self):
        """
        Default value when object is instantiated.
        If it is a callable, it will be called to get the new value,
        otherwise this value will be used as prototype and copied on each instance.
        """
        return self._default

    @property
    def handler(self):
        """
        Custom handler for serializing/deserializing this field value.
        """
        return self._handler

    @property
    def enum_as_str(self):
        """
        Determines if enums must be handled as string or int
        """
        return self._enum_as_str

    def default_val(self):
        """
        Returns a new instance of the default vault for this field.
        """
        default = self.default
        if callable(default):
            return default()
        elif default is not None:
            return copy.deepcopy(default)
        return None
