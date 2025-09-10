class Stats:
    def __init__(self):
        self.count = 0
        self.total = 0.0

    def add(self, x: float) -> None:
        self.count += 1
        self.total += x

    def mean(self) -> float:
        if self.count == 0:
            return 0.0
        return self.total / self.count

