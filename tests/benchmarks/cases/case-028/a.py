class SimpleCache:
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        if key in self._data:
            return self._data[key]
        self._data[key] = default
        return default

