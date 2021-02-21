from unittest import TestCase
from podm import JsonObject, Property, ArrayOf
from podm.util.mongo import QueryHelper


class Customer(JsonObject):
    first_name = Property(json="first-name")
    last_name = Property(json="last-name")
    tax_id = Property(json="tax-id")


class Item(JsonObject):
    product_id = Property(json="product-id")
    quantity = Property()
    unit_price = Property("unit-price")


class Invoice(JsonObject):
    customer = Property(type=Customer)
    items = Property(type=ArrayOf(Item))


class JsonPickleInvoice(JsonObject):
    __jsonpickle_format__ = True
    customer = Property(type=Customer)
    items = Property(type=ArrayOf(Item))


class TestQueryHelper(TestCase):
    def test_basic_operators(self):
        qhi = QueryHelper(Invoice)

        self.assertEqual({"items.product-id": 10}, (qhi.items.product_id == 10).expr())
        self.assertEqual({"items.product-id": {"$ne": 10}}, (qhi.items.product_id != 10).expr())
        self.assertEqual({"items.product-id": {"$lt": 10}}, (qhi.items.product_id < 10).expr())
        self.assertEqual({"items.product-id": {"$lte": 10}}, (qhi.items.product_id <= 10).expr())
        self.assertEqual({"items.product-id": {"$gt": 10}}, (qhi.items.product_id > 10).expr())
        self.assertEqual({"items.product-id": {"$gte": 10}}, (qhi.items.product_id >= 10).expr())
        self.assertEqual({"items.product-id": {"$in": [1, 2]}}, qhi.items.product_id.in_([1, 2]).expr())
        self.assertEqual({"items.product-id": {"$nin": [1, 2]}}, qhi.items.product_id.nin([1, 2]).expr())
        self.assertEqual({"items.product-id": {"$exists": True}}, (qhi.items.product_id.exists()).expr())

    def test_logic_operators(self):
        qhi = QueryHelper(Invoice)
        self.assertEqual(
            {"$and": [{"items.product-id": 10}, {"items.quantity": 5}]},
            qhi.and_(qhi.items.product_id == 10, qhi.items.quantity == 5).expr(),
        )
        self.assertEqual(
            {"items.product-id": 10, "items.quantity": 5},
            qhi.join(qhi.items.product_id == 10, qhi.items.quantity == 5).expr(),
        )
        self.assertEqual(
            {"$or": [{"items.product-id": 10}, {"items.quantity": 5}]},
            qhi.or_(qhi.items.product_id == 10, qhi.items.quantity == 5).expr(),
        )
        self.assertEqual(
            {"$nor": [{"items.product-id": 10}, {"items.quantity": 5}]},
            qhi.nor(qhi.items.product_id == 10, qhi.items.quantity == 5).expr(),
        )
        self.assertEqual(
            {"$not": {"items.product-id": 10}}, qhi.not_(qhi.items.product_id == 10).expr(),
        )

        self.assertEqual(
            {"$not": {"$and": [{"items.product-id": 10}, {"items.quantity": 5}]}},
            qhi.not_(qhi.and_(qhi.items.product_id == 10, qhi.items.quantity == 5)).expr(),
        )

    def test_array_ref(self):
        qhi = QueryHelper(Invoice)
        self.assertEqual({"items[0].product-id": 10}, (qhi.items[0].product_id == 10).expr())

    def test_json_pickle_format(self):
        qhi = QueryHelper(JsonPickleInvoice)

        self.assertEqual({"py/state.items.product-id": 10}, (qhi.items.product_id == 10).expr())

    def test_obj_type_expr(self):

        qhi = QueryHelper(Invoice)

        self.assertEqual({"py/object": "test.test_query_helper.Invoice"}, qhi.is_type_expr().expr())
