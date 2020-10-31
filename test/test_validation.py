from podm import JsonObject, Property, Validator, ValidationException
from unittest import TestCase
import traceback
import re


class ValidatorTest(JsonObject):
    __validate__ = True
    field_1 = Property(type=str, allow_none=False, validator="default")


class EmailValidator(Validator):
    def validate(self, obj, field, value):
        if not value:
            return f"{field} is mandatory"
        matched = re.match(r"[a-z0-9\.\-]+@[a-z0-9\.]+", value)
        if not matched:
            return f"Invalid email address {value}"
        return None


class ValidatorTest2(JsonObject):
    __validate__ = True
    email = Property(validator=EmailValidator())


class TestValidation(TestCase):
    def test_not_none(self):
        data = {"field_1": None}

        with self.assertRaises(ValidationException) as ctx:
            obj = ValidatorTest.from_dict(data)

        issues = ctx.exception.issues
        self.assertIsNotNone(issues)
        self.assertNotEqual(0, len(issues))

    def test_wrong_type(self):
        data = {"field_1": 1}

        with self.assertRaises(ValidationException) as ctx:
            obj = ValidatorTest.from_dict(data)

        issues = ctx.exception.issues
        self.assertIsNotNone(issues)
        self.assertNotEqual(0, len(issues))

    def test_right_type(self):
        data = {"field_1": "val"}
        try:
            obj = ValidatorTest.from_dict(data)
        except Exception as e:
            print(traceback.format_exc())
            self.assertTrue(False, str(e))

    def test_missing(self):
        data = {}
        with self.assertRaises(ValidationException) as ctx:
            obj = ValidatorTest.from_dict(data)

        issues = ctx.exception.issues
        self.assertIsNotNone(issues)
        self.assertNotEqual(0, len(issues))

    def test_custom_validator(self):

        data = {"email": None}
        with self.assertRaises(ValidationException) as ctx:
            obj = ValidatorTest2.from_dict(data)

        data = {"email": "xxxx"}
        with self.assertRaises(ValidationException) as ctx:
            obj = ValidatorTest2.from_dict(data)

        data = {"email": "xxxx@xxx.com"}
        try:
            obj = ValidatorTest2.from_dict(data)
        except Exception as e:
            self.assertTrue(False, str(e))
