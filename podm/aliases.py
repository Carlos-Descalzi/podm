_OBJ_CLASSES_BY_ALIAS = {}
_ALIASES_BY_OBJ_CLASS = {}


def add_alias(alias: str, obj_class_or_name: str):
    """
    Register an alias for a class or class name.
    This will be reflected on the field "py/object"
    parameters:
        alias: The alias to set for a given object type
        obj_class_or_name: Object class or class name.
    """
    obj_class_name = obj_class_or_name if isinstance(obj_class_or_name, str) else obj_class_or_name.object_type_name()
    _OBJ_CLASSES_BY_ALIAS[alias] = obj_class_name
    _ALIASES_BY_OBJ_CLASS[obj_class_name] = alias


def get_obj_class_name(name):
    return _OBJ_CLASSES_BY_ALIAS.get(name)


def get_alias(obj_class_name):
    return _ALIASES_BY_OBJ_CLASS.get(obj_class_name)
