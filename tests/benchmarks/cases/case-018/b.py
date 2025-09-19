class Lifo:
    def __init__(self):
        self._items = []

    def add(self, item):
        self._items.append(item)

    def remove(self):
        return self._items.pop()
