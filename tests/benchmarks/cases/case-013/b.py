def greatest_common_divisor(x, y):
    while y:
        x, y = y, x % y
    return x
