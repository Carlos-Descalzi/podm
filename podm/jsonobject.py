import copy
import importlib

from collections import OrderedDict
from .meta import Property, Handler
from enum import Enum, IntEnum

class MethodWrapper:
    def __init__(self, target, method):
        self._target = target
        self._method = method

    def __call__(self, *args, **kwargs):
        return self._method(self._target, *args, **kwargs)

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

class PropertyHandler:

    def __init__(self, obj_type, name, definition):
        self._name = name
        self._definition = definition
        self._field_name = '_%s' % name
        self._setter_name = 'set_%s' % name
        self._getter_name = 'get_%s' % name

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

    def json(self): return self._definition.json or self._name

    def handler(self): return self._definition.handler

    def field_name(self): return self._field_name

    def field_type(self): return self._definition.type

    def enum_as_str(self): return self._definition.enum_as_str

    def getter(self): return self._getter

    def getter_name(self): return self._getter_name

    def setter(self): return self._setter

    def setter_name(self): return self._setter_name

class JsonObject:
    """
    Base class for objects to be persisted as JSON.
    """
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
    def object_type_name(cls):
        """
        Returns the complete type name with module as prefix.
        """
        return '%s.%s' % (cls.__module__, cls.__name__)

    @classmethod
    def json_field_names(cls):
        """
        Returns the list of json field names
        """
        cls._check_init_class()
        return [p.json() for p in cls._properties.values()]

    @classmethod
    def _check_init_class(cls):
        """
        Perform the class initialization. Properties information are kept in the class
        """
        if not '_properties' in cls.__dict__:
            cls._properties = OrderedDict()
            cls._accessors = {}

            for _class in cls._get_class_hierarchy():
                properties = OrderedDict([
                        (k, PropertyHandler(_class, k, v)) for k, v in _class.__dict__.items() 
                        if isinstance(v, Property)])

                cls._accessors.update({p.setter_name():p.setter() for p in properties.values()})
                cls._accessors.update({p.getter_name():p.getter() for p in properties.values()})
                cls._properties.update(properties)

    def __str__(self):
        return self.__class__.__name__ + \
            ':' + \
            ';'.join(['%s=%s' % (k, v.get(self)) for k, v in self._properties.items()])

    def __repr__(self):
        return str(self)

    def __getattribute__(self, name):
        if name not in ['__class__', '__dict__', '_properties', '_accessors']:

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
        if name != '_properties' and name[0] != '_':
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
        if name == '__init__':
            return self.__class__.__dict__['__init__']

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
        return other and \
            self.__class__ == other.__class__ and \
            self.get_state_dict() == other.get_state_dict()

    def to_dict(self, dict_class=dict):
        """
        Returns the object as a JSON-friendly dictionary.
        Allows specify the dictionary class for the case when
        is required to use an ordered dictionary.
        The result dictionary contains a field 'py/object' holding the module and class name
        Parameters:
            dict_class: the type of dictionary object instantiated to return the data, default dict
        """
        result = dict_class()

        result['py/object'] = '%s.%s' % (self.__class__.__module__, self.__class__.__name__)
        #result['py/state'] = self.get_state_dict(dict_class)

        result.update(self.get_state_dict(dict_class))
            
        return result

    def get_state_dict(self, dict_class=dict):
        """
        Returns the JSON-like dictionary containing the state of this class.
        The result dictionary does not provide object information.
        Parameters:
            dict_class: the type of dictionary object instantiated to return the data, default dict
        """
        result = dict_class()
        for pname, prop in self._properties.items():
            val = self[pname]
            val = self._convert(prop, val, dict_class)
            result[prop.json()] = val
        return result

    def _convert(self, prop, value, dict_class=dict):
        if prop.handler():
            return prop.handler().encode(value)
        elif isinstance(value, JsonObject):
            return value.to_dict(dict_class)
        elif isinstance(value, OrderedDict):
            return OrderedDict([(k,self._convert(prop, v, dict_class)) for k, v in value.items()])
        elif isinstance(value, dict):
            return {k:self._convert(prop, v, dict_class) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._convert(prop, v, dict_class) for v in value]
        elif isinstance(value, Enum):
            if not isinstance(value, IntEnum) and prop.enum_as_str():
                return value.name
            return value.value
        return value

    def after_deserialize(self):
        """
        Callback to notify when the object has been instantiated and properly
        deserialized from a json representation
        """
        pass

    @classmethod
    def from_dict(cls, jsondata):
        """
        Returns an instance of this class based on a dictionary representation
        of JSON data. The object type is infered from the class from where this
        class method has been invoked
        """
        obj = JsonObject.__new__(cls)

        constructor = JsonObject._find_constructor(cls)
        constructor(obj)

        properties = {v.json():(k, v) for k, v in obj._properties.items()}

        # For backwards compatibility with jsonpickle
        data = jsondata.get('py/state', jsondata)

        for k, v in data.items():
            if k not in ['py/object', '_id']:
                pname, prop = properties.get(k)
                if prop:

                    handler = prop.handler()
                    field_type = prop.field_type()

                    if handler:
                        obj[pname] = handler.decode(v)
                    elif field_type:
                        if issubclass(field_type, Enum):
                            if isinstance(v,str):
                                obj[pname] = field_type[v]
                            else:
                                # TODO: is there a better way?
                                for m in list(field_type):
                                    if m.value == v:
                                        obj[pname] = m
                                        break
                        else:
                            obj[pname] = field_type.from_dict(v)
                    else:
                        obj[pname] = JsonObject.parse(v, cls.__module__)
        
        if hasattr(obj, '_after_deserialize'):
            obj._after_deserialize()

        return obj
    
    @staticmethod
    def parse(val, module_name='__main__'):
        """
        Parses a dictionary and returns the appropiate object instance.
        Note the input dictionary must contain 'py/object' field to detect
        the appropiate object class, otherwise it will return a dictionary 
        """
        if isinstance(val, dict):
            if 'py/object' in val:
                obj_type = JsonObject._resolve_obj_type(val['py/object'], module_name)
                state = val.get('py/state', val) # fallback to the same dictionary
                return obj_type.from_dict(state)
            else:
                return {k:JsonObject.parse(v, module_name) for k, v in val.items()} 
        elif isinstance(val, list):
            return [JsonObject.parse(v, module_name) for v in val]
        
        return val

    @staticmethod
    def _find_constructor(obj_class):
        if '__init__' in obj_class.__dict__:
            return obj_class.__dict__['__init__']

        for item in obj_class.__bases__:
            c = JsonObject._find_constructor(item)
            if c: return c

        return None

    @staticmethod
    def _resolve_obj_type(type_name, module_name):

        if '.' in type_name:
            i = type_name.rfind('.')
            mod_name = type_name[0:i]
            obj_type = type_name[i+1:]

            module = importlib.import_module(mod_name)
            return module.__getattribute__(obj_type)
        else:
            module = importlib.import_module(module_name)
            return module.__getattribute__(type_name)

    @classmethod
    def _get_class_hierarchy(cls):
        current_class = cls
        hierarchy = []
        while current_class != JsonObject:
            hierarchy.insert(0, current_class)
            current_class = current_class.__bases__[0]
        return hierarchy

            
