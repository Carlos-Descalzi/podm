from podm.meta import CollectionOf
from abc import ABCMeta, abstractmethod


class BaseExpr(metaclass=ABCMeta):
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


class JoinedAnd(And):
    def expr(self):
        result = {}

        for expr in self._expressions:
            result.update(expr.expr())

        return result


class Or(LogicalOperation):
    _operator = "$or"


class Nor(LogicalOperation):
    _operator = "$nor"


class Not(LogicalOperation):
    _operator = "$not"

    def expr(self):
        # Here it takes only first argument
        return {self._operator: self._expressions.expr()}


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


class ArrayItem(BaseField):
    """
    Array item referencing.
    """

    def __init__(self, parent, field, key):
        super().__init__(parent, field)
        self._key = key

    def path(self):
        return self._parent.path() + [self]

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

    def eq(self, value):
        """
        Same as __eq__
        """
        return Eq(self, value)

    def __eq__(self, value):
        """
        $eq operator, translates expression a == b into {'a':b}
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


class QueryHelper:
    """
    Utility class which allows making Mongo queries
    in a typed way, allowing abstracting implementation from
    real model.

    Having a some classes like this:

        class Item(JsonObject):
            product_id = Property(json="product-id")
            quantity = Property()

        class Invoice(JsonObject):
            items = Property(type=ArrayOf(Item))

    it is possible to create expressions like this:

        qhi = QueryHelper(Invoice)
        expression = qhi.and_(qhi.items.product_id == "1000", qhi.items.quantity < 10).expr()

    which will translate into this:

        {'$and': [{'items.product-id':'1000'},{'items.quantity': {'$lt':10}}]}

    Another example:
        expression = (qhi.items.quantity == 100).expr()
    
    while translate into this:

        {'items.quantity':100}

    """

    def __init__(self, obj_type):
        self._obj_type = obj_type

    def name(self):
        return "py/state" if self._obj_type.__jsonpickle_format__ else ""

    def field_path(self):
        return [self] if self._obj_type.__jsonpickle_format__ else []

    def __getattr__(self, name):
        """
        Returns a field instance pointing to the expected field of the class
        """
        return Field(self, getattr(self._obj_type, name), name)

    def and_(self, *args):
        """
        $and operator
        """
        return And(self, args)

    def join(self, *args):
        """
        Join all expressions passed as parameter into one single dictionary,
        this is the default $and operation.
        """
        return JoinedAnd(self, args)

    def or_(self, *args):
        """
        $or operator
        """
        return Or(self, args)

    def nor(self, *args):
        """
        $nor operator
        """
        return Nor(self, args)

    def not_(self, arg):
        """
        $not operator
        """
        return Not(self, arg)

    def is_type_expr(self):
        """
        Return an expression for checking document's py/object value.
        This is translated into: {'py/object' : 'module.classname'}
        """
        return ObjectTypeExpr(self)
