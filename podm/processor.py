# vim:ts=4:sw=4:expandtab
__author__ = "Carlos Descalzi"

from abc import ABCMeta, abstractmethod
from typing import Any, Tuple


class Processor(metaclass=ABCMeta):
    """
    Allows to reformat data before serializing/deserializing
    """

    @abstractmethod
    def when_from_dict(self, key: str, value: Any) -> Tuple[str, Any]:
        """
        Called when deserializing object.
        Returns key, value
        """

    @abstractmethod
    def when_to_dict(self, key: str, value: Any) -> Tuple[str, Any]:
        """
        Called when serializing object.
        Returns key, value.
        """


class DefaultProcessor(Processor):
    """
    Dummy implementation, does not do any processing.
    """

    def when_from_dict(self, key, value):
        return key, value

    def when_to_dict(self, key, value):
        return key, value
