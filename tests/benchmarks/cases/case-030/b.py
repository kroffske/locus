def argmin(xs):
    idx = 0
    val = xs[0]
    for i in range(1, len(xs)):
        cur = xs[i]
        if cur < val:
            val = cur
            idx = i
    return idx

