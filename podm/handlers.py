# vim:ts=4:sw=4:expandtab
from .meta import Handler

class ListStringHandler(Handler):
    """
    Convert JSON list to and from list of given class_type

    class_type must implement str conversion to encode to JSON.
    """

    def __init__(self, class_type):
        self.class_type = class_type

    def encode(self, objects):
        return [str(obj) for obj in objects]

    def decode(self, string_list):
        return [self.class_type(string) for string in string_list]
