from typing import AnyStr, Any


class HandlerLRUCache(object):
    keys = []

    cache = {}

    def __init__(self, handler_cache_capacity: int = None):
        self.handler_cache_capacity = handler_cache_capacity

    def is_head(self, key: AnyStr):
        if self.keys.index(key) == 0:
            return True
        else:
            return False

    def get(self, key: AnyStr):
        if key in self.keys:
            self.keys.remove(key)
            self.keys.insert(0, key)
            return self.cache[key]
        else:
            return None

    def set(self, key: AnyStr, value: Any):
        if key not in self.keys:
            if len(self.keys) >= self.handler_cache_capacity:
                deleted_key = self.keys.pop(-1)
                del self.cache[deleted_key]
            self.keys.insert(0, key)
            self.cache[key] = value
        else:
            if not self.is_head(key):
                self.keys.remove(key)
                self.keys.insert(0, key)
            self.cache[key] = value

    def __get__(self, instance, owner):
        return self.__class__(
            instance.handler_cache_capacity
        )
