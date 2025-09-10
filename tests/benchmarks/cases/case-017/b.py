def fibonacci(k: int) -> int:
    if k < 2:
        return k
    return fibonacci(k - 1) + fibonacci(k - 2)

