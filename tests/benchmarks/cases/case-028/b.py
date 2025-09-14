class SimpleCache:
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        val = self._data.get(key)
        if val is not None:
            return val
        self._data[key] = default
        return default
