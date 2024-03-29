# vim:ts=4:sw=4:expandtab
__author__ = "Carlos Descalzi"

from abc import ABCMeta, abstractmethod
from enum import Enum
from .meta import Handler, ArrayOf, MapOf
from typing import Any, Type, Mapping


class PropertyHandler(metaclass=ABCMeta):
    def __init__(self, obj_type, name, definition):
        self._obj_type = obj_type
        self._name = name
        self._definition = definition

    def name(self):
        return self._name

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

    @abstractmethod
    def field_name(self) -> str:
        """
        Return the field name.
        """

    def json_field_type(self, type_definitions={}, deep=True, base_schema_url=None):
        """
        Converts actual field type into javascript types.
        Subclasses may extend it
        """
        field_type = self.field_type()

        return self._json_field_type(field_type, type_definitions, deep, base_schema_url)

    def _json_field_type(self, field_type, type_definitions={}, deep=True, base_schema_url=None):
        if field_type is None:
            return "object"
        if field_type == str:
            return "string"
        elif field_type == bool:
            return "boolean"
        elif field_type in [int, float]:
            return "number"
        elif field_type == list:
            return "array"
        elif isinstance(field_type, ArrayOf):
            # TODO Fix this mess
            f_type = self._json_field_type(field_type.type, type_definitions, deep, base_schema_url)
            if isinstance(f_type, str):
                f_type = {"type": f_type}
            return {"type": "array", "items": f_type}
        elif isinstance(field_type, MapOf):
            # TODO Fix this mess
            f_type = self._json_field_type(field_type.type, type_definitions, deep, base_schema_url)
            if isinstance(f_type, str):
                f_type = {"type": f_type}
            return {"type": "object", "patternProperties": {".*": f_type}}
        elif issubclass(field_type, Enum):
            return "number"
        elif field_type.__name__ in type_definitions:
            if deep:
                return self._get_ref(field_type, deep, base_schema_url)
            else:
                return "object"
        elif base_schema_url:
            return self._get_ref(field_type, deep, base_schema_url)
        else:
            return "object"

    def _get_ref(self, field_type, deep, base_schema_url):
        if deep:
            return {"$ref": f"#/definitions/{field_type.__name__}"}
        elif base_schema_url:
            return {"$ref": f"{base_schema_url}/{field_type.__name__}"}

        return None

    def schema(self, type_definitions={}, deep=True, base_schema_url=None) -> Mapping:
        """
        Returns the json schema definition of the property
        """
        schema_ref = self._definition.schema_ref

        if schema_ref:
            return {"$ref": schema_ref}
        field_type = self.json_field_type(type_definitions, deep, base_schema_url)
        if isinstance(field_type, str):
            return {"type": field_type}
        return field_type

    def validator(self):
        return None

    def allow_none(self):
        return True

    @property
    def group(self):
        return None

    def format(self):
        return None

    def pattern(self):
        return None


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

    @abstractmethod
    def enum_as_str(self) -> bool:
        """
        Boolean flag that determines if flags are stored/retrieved
        as string literals or integers.
        """

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
        super().__init__(obj_type, name, definition)
        self._field_name = "_%s" % name
        self._setter_name = "set_%s" % name
        self._getter_name = "get_%s" % name

        getter = obj_type.__dict__.get(self._getter_name)
        self._getter = getter or DefaultGetter(self._field_name)

        setter = obj_type.__dict__.get(self._setter_name)
        self._setter = setter or DefaultSetter(self._field_name)

    def init(self, target, value):
        self.set(target, value if value is not None else self._definition.default_val())

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

    def validator(self):
        return self._definition.validator

    def allow_none(self):
        return self._definition.allow_none

    @property
    def group(self):
        return self._definition.group

    def format(self):
        return self._definition.format

    def pattern(self):
        return self._definition.pattern

    def schema(self, type_definitions={}, deep=True, base_schema_url=None):

        if self._definition.schema:
            return self._definition.schema

        schema = super().schema(type_definitions, deep, base_schema_url)

        default = self._definition.default
        if default is not None and not callable(default):
            schema["default"] = self._definition.default

        if self._definition.title:
            schema["title"] = self._definition.title

        if self._definition.pattern:
            schema["pattern"] = self._definition.pattern
        if self._definition.format:
            schema["format"] = self._definition.format

        if self._definition.description:
            schema["description"] = self._definition.description

        if (
            self.field_type()
            and isinstance(self.field_type(), type)
            and issubclass(self.field_type(), Enum)
            and self.enum_as_str
        ):
            schema["type"] = "string"
            schema["enum"] = self.field_type()._member_names_

        return schema
