from .expressions import (
    BaseExpr,
    ObjectTypeExpr,
    SetExpr,
    Join,
    Projection,
    And,
    Or,
    Nor,
    Not,
    Field,
    SortExpr,
    SetOrInsertExpr,
)


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
        expression = qhi(qhi.items.product_id == "1000", qhi.items.quantity < 10)

    which will translate into this:

        {'items.product-id':'1000', 'items.quantity': {'$lt':10}}

    Another example:
        expression = (qhi.items.quantity == 100)
    
    while translate into this:

        {'items.quantity':100}

    All expressions are comparable with dictionaries or lists depending the case

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

    def __call__(self, *args):
        """
        Join all expressions passed as parameter into one single dictionary,
        this is the default $and operation.
        """
        return Join(self, args)

    def project(self, *fields):
        """
        Builds a query projection expression dictionary.
        As input it receives a list of fields, for those which is required on the result, 
        or a tuple (field, False), for those fields not required on the result.
        """
        return Projection(fields)

    def sort(self, *sort_exprs):
        """
        Builds a list of (field, sort), by receiving a list of field.asc()/desc().
        """
        return list(map(SortExpr.expr, sort_exprs))

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

    def type_expr(self):
        """
        Return an expression for checking document's py/object value.
        This is translated into: {'py/object' : 'module.classname'}
        """
        return ObjectTypeExpr(self)

    def set(self, *args):
        return SetExpr(self, args)

    def set_or_insert(self, *args):
        return SetOrInsertExpr(self, args)
