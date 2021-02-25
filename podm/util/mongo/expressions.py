from podm.meta import CollectionOf
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping


class BaseExpr(Mapping, metaclass=ABCMeta):
    """
    Interface for expressions.
    """

    @abstractmethod
    def expr(self):
        """
        Convert this expression into a dictionary representing
        a mongo query expression.
        """
        pass

    def keys(self):
        return self.expr().keys()

    def items(self):
        return self.expr().items()

    def values(self):
        return self.expr().values()

    def __getitem__(self, key):
        return self.expr()[key]

    def __len__(self):
        return 1

    def __hash__(self):
        return hash(self.expr())

    def __eq__(self, other):
        if isinstance(other, Expr):
            return self.expr() == other.expr
        elif isinstance(other, dict):
            return self.expr() == other
        return False

    def __str__(self):
        return str(self.expr())

    def __repr__(self):
        return str(self)

    def __contains__(self, key):
        return key in self.expr()

    def get(self, key, default=None):
        return self.expr().get(key, default)

    def __iter__(self):
        return iter(self.expr())


class Expr(BaseExpr):
    def __init__(self, field, value):
        self._field = field
        self._value = value


class Comparation(Expr):
    _comparator = None

    def expr(self):
        return {self._field.path(): {self._comparator: self._value}}


class Eq(Comparation):
    _comparator = "$eq"  # not used for this particular case in favor of {k:v}

    def expr(self):
        return {self._field.path(): self._value}


class Ne(Comparation):
    _comparator = "$ne"


class Lt(Comparation):
    _comparator = "$lt"


class Le(Comparation):
    _comparator = "$lte"


class Gt(Comparation):
    _comparator = "$gt"


class Ge(Comparation):
    _comparator = "$gte"


class In(Comparation):
    _comparator = "$in"


class Nin(Comparation):
    _comparator = "$nin"


class Exists(Comparation):
    _comparator = "$exists"


class Operation(BaseExpr):
    def __init__(self, parent, expressions):
        self._parent = parent
        self._expressions = expressions


class LogicalOperation(Operation):
    _operator = None

    def expr(self):
        return {self._operator: [i.expr() for i in self._expressions]}


class And(LogicalOperation):
    _operator = "$and"


class Join(And):
    def expr(self):
        result = {}

        for expr in self._expressions:
            result.update(expr.expr())

        return result


class Projection(BaseExpr):
    def __init__(self, fields):
        self._fields = fields

    def expr(self):
        return {f.path(): v for (f, v) in map(lambda x: (x, 1) if isinstance(x, BaseField) else x, self._fields)}


class Or(LogicalOperation):
    _operator = "$or"


class Nor(LogicalOperation):
    _operator = "$nor"


class Not(LogicalOperation):
    _operator = "$not"

    def expr(self):
        # Here it takes only first argument
        return {self._operator: self._expressions.expr()}


class SortExpr(BaseExpr):
    ASCENDING = 1
    DESCENDING = -1

    def __init__(self, field, val):
        self._field = field
        self._val = val

    def expr(self):
        return (self._field.path(), self._val)


class BaseSetExpr(BaseExpr):
    _operator = None

    def __init__(self, parent, set_dict):
        self._parent = parent
        self._set_dict = set_dict

    def expr(self):
        return {self._operator: dict([v.expr() for v in self._set_dict])}


class SetExpr(BaseSetExpr):
    _operator = "$set"


class SetOrInsertExpr(BaseSetExpr):
    _operator = "$setOrInsert"


class SetFieldExpr(BaseExpr):
    def __init__(self, field, val):
        self._field = field
        self._val = val

    def expr(self):
        return (self._field.path(), self._val)


class BaseField:
    def __init__(self, parent, field):
        self._parent = parent
        self._field = field

    def field_path(self):
        return self._parent.field_path() + [self]

    def _add_dot(self):
        return True

    def path(self):
        result = []
        for item in self.field_path():
            if result and item._add_dot():
                result.append(".")
            result.append(item.name())
        return "".join(result)

    def __getattr__(self, name):
        field_type = self._field.type

        if isinstance(field_type, CollectionOf):
            field_type = field_type.type

        return Field(self, getattr(field_type, name), name)

    def __getitem__(self, key):
        return ArrayItem(self, self._field, key)

    def __eq__(self, value):
        """
        $eq operator, translates expression a == b into {'a':b}
        """
        return Eq(self, value)

    def eq(self, value):
        """
        Same as __eq__
        """
        return Eq(self, value)

    def __ne__(self, value):
        """
        $ne operator, traslates expression a < b into {'a' : {'$lt': b} }
        """
        return Ne(self, value)

    def __lt__(self, value):
        """
        $lt operator, traslates expression a < b into {'a' : {'$lt': b} }
        """
        return Lt(self, value)

    def __le__(self, value):
        """
        $lte operator, traslates expression a <= b into {'a' : {'$lte': b} }
        """
        return Le(self, value)

    def __gt__(self, value):
        """
        $gt operator, traslates expression a > b into {'a' : {'$gt': b} }
        """
        return Gt(self, value)

    def __ge__(self, value):
        """
        $gte operator, traslates expression a > b into {'a' : {'$gte': b} }
        """
        return Ge(self, value)

    def in_(self, value):
        """
        $in operator
        """
        return In(self, value)

    def nin(self, value):
        """
        $nin operator
        """
        return Nin(self, value)

    def exists(self, val=True):
        """
        $exists operator, expects boolean argument.
        """
        return Exists(self, val)

    def asc(self):
        """
        ascending sort expression
        """
        return SortExpr(self, SortExpr.ASCENDING)

    def desc(self):
        """
        descending sort expression
        """
        return SortExpr(self, SortExpr.DESCENDING)

    def __call__(self, arg):
        return SetFieldExpr(self, arg)


class ArrayItem(BaseField):
    """
    Array item referencing.
    """

    def __init__(self, parent, field, key):
        super().__init__(parent, field)
        self._key = key

    def name(self):
        return "[" + (f"'{self._key}'" if isinstance(self._key, str) else str(self._key)) + "]"

    def _add_dot(self):
        return False


class ObjectTypeExpr(BaseField):
    def __init__(self, parent):
        super().__init__(parent, None)

    def name(self):
        return "py/object"

    def expr(self):
        return {self.name(): self._parent._obj_type.object_type_name()}


class Field(BaseField):
    """
    Field referencing.
    """

    def __init__(self, parent, field, name):
        super().__init__(parent, field)
        self._field_name = name

    def name(self):
        """
        Actual name of this field
        """
        return self._field.json or self._field_name
