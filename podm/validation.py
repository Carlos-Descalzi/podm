from abc import ABCMeta, abstractmethod
from typing import Any
from .meta import MapOf, ArrayOf


class ValidationException(Exception):
    def __init__(self, issues={}):
        """
        Parameters:
        issues: a dictionary of field name: message for validation issues.
        """
        super().__init__()
        self._issues = issues

    @property
    def issues(self):
        """
        Returns a dictionary of field name : message indicating the validation issues.
        """
        return self._issues

    def __str__(self):
        return "ValidationException: " + ", ".join(
            [f"{k}: {v}" for k, v in self._issues.items()]
        )


class Validator(metaclass=ABCMeta):
    """
    Interface for validators
    """

    @abstractmethod
    def validate(self, obj: object, field: str, value: Any) -> str:
        """
        Validates a field value.
        Returns None when validation passes, or a message indicating the issue.
        """
        pass


class TypeValidator(Validator):
    """
    Validates that the value being set is of the type
    declared in the class metadata
    """

    def validate(self, obj, field, value):
        prop_descriptor = getattr(obj.__class__, field)

        if value is None and not prop_descriptor.allow_none:
            return f"{field} must be not null"

        if isinstance(prop_descriptor.type, MapOf):
            if not isinstance(value, dict):
                return f"{field} value '{value}' is not a dictionary-like object"

        if isinstance(prop_descriptor.type, ArrayOf):
            if not isinstance(value, list):
                return f"{field} value '{value}' is not a list-like object"

        if not isinstance(value, prop_descriptor.type):
            return f"{field} value '{value}' is not of type {prop_descriptor.type}"
