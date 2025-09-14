def sum_of_squares(xs):
    s = 0
    for v in xs:
        s += v * v
    # tiny change: alias var name only
    return s
