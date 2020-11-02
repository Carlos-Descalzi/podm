# vim:ts=4:sw=4:expandtab
__author__ = "Carlos Descalzi"

import copy
import importlib
from collections import OrderedDict
from abc import ABCMeta, abstractmethod
from .meta import Property, Handler, ArrayOf, MapOf
from .processor import DefaultProcessor
from .properties import DefaultPropertyHandler, RichPropertyHandler
from enum import Enum, IntEnum
from .validation import ValidationException, TypeValidator
from .schema import SchemaBuilder

_DEFAULT_PROCESSOR = DefaultProcessor()
_DEFAULT_VALIDATOR = TypeValidator()


def _find_constructor(obj_class):
    if "__init__" in obj_class.__dict__:
        return obj_class.__dict__["__init__"]

    for item in obj_class.__bases__:
        c = _find_constructor(item)
        if c:
            return c

    return None


def _resolve_obj_type(type_name, module_name):

    if "." in type_name:
        i = type_name.rfind(".")
        mod_name = type_name[0:i]
        obj_type = type_name[i + 1 :]

        module = importlib.import_module(mod_name)
        return module.__getattribute__(obj_type)
    else:
        module = importlib.import_module(module_name)
        return module.__getattribute__(type_name)


def _get_class_hierarchy(cls):
    current_class = cls
    hierarchy = []
    while hasattr(current_class, "__json_object__"):
        hierarchy.insert(0, current_class)
        current_class = current_class.__bases__[0]
    return hierarchy


class MethodWrapper:
    def __init__(self, target, method):
        self._target = target
        self._method = method

    def __call__(self, *args, **kwargs):
        return self._method(self._target, *args, **kwargs)


class Introspector:
    def get_properties(self, obj_class):
        pass


class DefaultIntrospector(Introspector):
    def get_properties(self, obj_class):

        properties = OrderedDict()

        handler_class = self.property_handler_class()

        for _class in _get_class_hierarchy(obj_class):
            class_properties = OrderedDict(
                [(k, handler_class(_class, k, v)) for k, v in _class.__dict__.items() if isinstance(v, Property)]
            )

            properties.update(class_properties)

        return properties

    def property_handler_class(self):
        return DefaultPropertyHandler


class BaseJsonObject:
    """
    Base support class for converting objects to json.
    """

    __json_object__ = True
    __jsonpickle_format__ = False
    __validate__ = False
    __add_type_identifier__ = True

    _introspector = DefaultIntrospector()

    def __new__(cls, **kwargs):
        cls._check_init_class()
        obj = object.__new__(cls)
        obj.__init__(**kwargs)

        return obj

    def __init__(self, **kwargs):
        """
        kwargs should contain values for the fields, parameters must match declared object property
        names. Other parameters are ignored.
        """
        for name, prop in self._properties.items():
            prop.init(self, kwargs.get(name))

    @classmethod
    def _check_init_class(cls):
        """
        Perform the class initialization. Properties information are kept in the class
        """
        if not "_properties" in cls.__dict__:
            cls._properties = cls._introspector.get_properties(cls)

    @classmethod
    def property_names(cls):
        """
        Returns the list of property names
        """
        cls._check_init_class()
        return cls._properties.keys()

    @classmethod
    def properties(cls):
        cls._check_init_class()
        return cls._properties

    @classmethod
    def json_field_names(cls):
        """
        Returns the list of json field names
        """
        cls._check_init_class()
        return [p.json() for p in cls._properties.values()]

    @classmethod
    def schema(cls):
        """
        Returns a dictionary representing the json schema.
        """
        cls._check_init_class()

        return SchemaBuilder(cls).build()

    @classmethod
    def object_type_name(cls):
        """
        Returns the complete type name with module as prefix.
        """
        return "%s.%s" % (cls.__module__, cls.__name__)

    def to_dict(self, dict_class=dict, processor=_DEFAULT_PROCESSOR, add_type_identifier=None):
        """
        Returns the object as a JSON-friendly dictionary.
        Allows specify the dictionary class for the case when
        is required to use an ordered dictionary.
        The result dictionary contains a field 'py/object' holding the module and class name
        Parameters:
            dict_class: the type of dictionary object instantiated to return the data, default dict
            processor: A processor for key/value pairs
        """
        result = dict_class()

        add_type_identifier = add_type_identifier or self.__add_type_identifier__

        if add_type_identifier:
            result["py/object"] = self.object_type_name()

        state_dict = self.get_state_dict(dict_class, processor, add_type_identifier)
        if self.__jsonpickle_format__:
            result["py/state"] = state_dict
        else:
            result.update(state_dict)

        return result

    def get_state_dict(self, dict_class=dict, processor=_DEFAULT_PROCESSOR, add_type_identifier=True):
        """
        Returns the plain JSON-like dictionary containing the state of this class.
        The result dictionary does not provide object type information nor any jsonpickle-like field.
        Parameters:
            dict_class: the type of dictionary object instantiated to return the data, default dict
            processor: A processor for key/value pairs
        """
        result = dict_class()
        for pname, prop in self._properties.items():
            if hasattr(self, "__getitem__"):
                val = self[pname]
            else:
                val = prop.get(self)

            val = self._convert(prop, val, dict_class, processor, add_type_identifier)
            key, val = processor.when_to_dict(prop.json(), val)
            result[key] = val
        return result

    def after_deserialize(self):
        """
        Callback to notify when the object has been instantiated and properly
        deserialized from a json representation
        """
        pass

    def _convert(
        self, prop, value, dict_class=dict, processor=_DEFAULT_PROCESSOR, add_type_identifier=True,
    ):
        handler = prop.handler()
        if handler:
            return handler.encode(value)
        elif isinstance(value, BaseJsonObject):
            return value.to_dict(dict_class, processor, add_type_identifier)
        elif isinstance(value, OrderedDict):
            return OrderedDict(
                [(k, self._convert(prop, v, dict_class, processor, add_type_identifier),) for k, v in value.items()]
            )
        elif isinstance(value, dict):
            processed = dict([processor.when_to_dict(k, v) for k, v in value.items()])
            return {k: self._convert(prop, v, dict_class, processor, add_type_identifier) for k, v in processed.items()}
        elif isinstance(value, list):
            return [self._convert(prop, v, dict_class, processor, add_type_identifier) for v in value]
        elif isinstance(value, Enum):
            if not isinstance(value, IntEnum) and prop.enum_as_str():
                return value.name
            return value.value
        return value

    def _after_deserialize(self):
        """
        Callback to allow do post-deserialization operations on the object.
        """
        pass

    @classmethod
    def from_dict(cls, jsondata, processor=_DEFAULT_PROCESSOR, validate=None):
        """
        Returns an instance of this class based on a dictionary representation
        of JSON data. The object type is infered from the class from where this
        class method has been invoked
        Parameters:
            jsondata: A dictionary structure representing the json data.
            processor: A custom processor for field deserialization.
            validate: indicates if should validate or not, overrides class field __validate__
        """
        if jsondata is None:
            return None

        obj = cls.__new__(cls)

        constructor = _find_constructor(cls)
        constructor(obj)

        properties = {v.json(): (k, v) for k, v in obj._properties.items()}

        # For backwards compatibility with jsonpickle
        data = jsondata.get("py/state", jsondata)

        primitive = lambda p: p.field_type() in [bool, int, float, str]

        validate = validate or cls.__validate__

        issues = {}

        required = set([k for k, v in properties.values() if not v.allow_none()])

        for k, v in data.items():
            if k not in ["py/object", "_id"]:
                try:
                    required.remove(k)
                except:
                    pass
                k, v = processor.when_from_dict(k, v)

                if k in properties:
                    pname, prop = properties.get(k)

                    handler = prop.handler()
                    if handler:
                        v = handler.decode(v)
                        cls._set_field(obj, pname, prop, v)
                    elif prop.field_type() and not primitive(prop):
                        v = cls._handle_field_type(obj, pname, prop, v)
                    else:
                        v = BaseJsonObject.parse(v, cls.__module__)
                        cls._set_field(obj, pname, prop, v)

                    if validate:
                        issue = cls._validate(obj, prop, v)
                        if issue:
                            issues[k] = issue

        if validate:
            if required:
                issues.update({k: f"Field {k} is required" for k in required})
            if issues:
                raise ValidationException(issues)

        obj._after_deserialize()

        return obj

    @classmethod
    def _validate(cls, obj, prop, value):
        validator = prop.validator()

        if validator:
            if validator == "default":
                validator = _DEFAULT_VALIDATOR
            return validator.validate(obj, prop.name(), value)
        return None

    @classmethod
    def _set_field(cls, obj, pname, prop, value):
        if hasattr(obj, "__setitem__"):
            obj[pname] = value
        else:
            prop.set(obj, value)

    @classmethod
    def _handle_field_type(cls, obj, pname, prop, value):
        field_type = prop.field_type()
        if isinstance(field_type, ArrayOf):
            value = list(map(field_type.type.from_dict, value))
            cls._set_field(obj, pname, prop, value)
        elif isinstance(field_type, MapOf):
            value = {ok: field_type.type.from_dict(ov) for ok, ov in value.items()}
            cls._set_field(obj, pname, prop, value)
        elif issubclass(field_type, Enum):
            if isinstance(value, str):
                value = field_type[value]
                cls._set_field(obj, pname, prop, value)
            else:
                # TODO: is there a better way?
                for m in list(field_type):
                    if m.value == value:
                        cls._set_field(obj, pname, prop, m)
                        value = m
                        break
        else:
            value = field_type.from_dict(value)
            cls._set_field(obj, pname, prop, value)

        return value

    @staticmethod
    def parse(val, module_name="__main__", processor=_DEFAULT_PROCESSOR):
        """
        Parses a dictionary and returns the appropiate object instance.
        Note the input dictionary must contain 'py/object' field to detect
        the appropiate object class, otherwise it will return a dictionary 
        """
        if isinstance(val, dict):
            if "py/object" in val:
                obj_type = _resolve_obj_type(val["py/object"], module_name)
                state = val.get("py/state", val)  # fallback to the same dictionary
                return obj_type.from_dict(state, processor)
            else:
                processed = dict([processor.when_from_dict(k, v) for k, v in val.items()])
                return {k: BaseJsonObject.parse(v, module_name, processor) for k, v in processed.items()}
        elif isinstance(val, list):
            return [JsonObject.parse(v, module_name, processor) for v in val]

        return val


class JsonObject(BaseJsonObject):
    """
    This class extends BaseJsonObject by adding features like property accessors and default values
    """

    @classmethod
    def _check_init_class(cls):
        super()._check_init_class()
        if not "_accessors" in cls.__dict__:
            cls._accessors = {}

            for p in cls._properties.values():
                if not isinstance(p, RichPropertyHandler):
                    raise Exception("This class needs RichPropertyHandler instances to handle properties")
                if p.setter():
                    cls._accessors[p.setter_name()] = p.setter()
                if p.getter():
                    cls._accessors[p.getter_name()] = p.getter()

    def __str__(self):
        return (
            self.__class__.__name__ + ":" + ";".join(["%s=%s" % (k, v.get(self)) for k, v in self._properties.items()])
        )

    def __repr__(self):
        return str(self)

    def __getattribute__(self, name):

        if name not in ["__class__", "__dict__", "_properties", "_accessors"]:
            if name in self._properties:
                handler = self._properties[name]
                return handler.get(self)

            if name in self._accessors:
                return MethodWrapper(self, self._accessors[name])

        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        """
        Customized accesor for setting object attributes
        If property exists, it is set into its internal state.
        """
        if name != "_properties" and name[0] != "_":
            if name in self._properties:
                self._properties[name].set(self, value)
            elif name in self.__class__.__dict__:
                prop = self.__class__.__dict__[name]
                if isinstance(prop, property) and prop.fset:
                    prop.fset(self, value)
                else:
                    raise AttributeError(name)
            else:
                raise AttributeError(name)
        else:
            self.__dict__[name] = value

    def __getattr__(self, name):
        """
        Customized accessor for object attributes
        """

        if name == "__init__":
            return self.__class__.__dict__["__init__"]

        if name in self._properties:
            return self._properties[name].get(self)

        raise AttributeError(name)

    def __setitem__(self, name, value):
        """
        Allow access the object state as a dictionary
        """
        if name in self._properties:
            self._properties[name].set(self, value)
        else:
            raise KeyError(name)

    def __getitem__(self, name):
        """
        Allows set object fields as a dictionary
        """
        if name in self._properties:
            return self._properties[name].get(self)
        raise KeyError(name)

    def __eq__(self, other):
        """
        Defines its equality by same class and same state dictionaries
        """
        return other and self.__class__ == other.__class__ and self.get_state_dict() == other.get_state_dict()
