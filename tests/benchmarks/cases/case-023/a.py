class Stats:
    def __init__(self):
        self.total = 0.0
        self.count = 0

    def add(self, x: float) -> None:
        self.total += x
        self.count += 1

    def mean(self) -> float:
        return self.total / self.count if self.count else 0.0

