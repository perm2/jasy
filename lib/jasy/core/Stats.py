#
# Jasy - Storage for statistics data
# Copyright 2010-2011 Sebastian Werner
#

__all__ = ["Stats"]

class Stats():
    """
    Used by core/Variables.py to store the resulting statistics data efficiently.
    """

    __slots__ = ["name", "params", "declared", "accessed", "modified", "shared", "unused", "packages"]
    
    def __iter__(self):
        for field in self.__slots__:
            yield field

    def __getitem__(self, key):
        if key == "name":
            return self.name
        elif key == "params":
            return self.params
        elif key == "declared":
            return self.declared
        elif key == "accessed":
            return self.accessed
        elif key == "modified":
            return self.modified
        elif key == "shared":
            return self.shared
        elif key == "unused":
            return self.unused
        elif key == "packages":
            return self.packages

        raise KeyError("Unknown key: %s" % key)

    def __init__(self):
        self.name = None
        self.params = set()
        self.declared = set()
        self.accessed = {}
        self.modified = set()
        self.shared = {}
        self.unused = set()
        self.packages = {}
        
    def increment(self, name, by=1):
        """ Small helper so simplify adding variables to "accessed" dict """
        if not name in self.accessed:
            self.accessed[name] = by
        else:
            self.accessed[name] += by
            