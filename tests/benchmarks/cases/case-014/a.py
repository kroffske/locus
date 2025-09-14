class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def dist2(self):
        return self.x * self.x + self.y * self.y
