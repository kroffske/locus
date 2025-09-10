def clamp(x, lo, hi):
    if x > hi:
        return hi
    if x < lo:
        return lo
    return x

