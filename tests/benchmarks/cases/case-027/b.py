def sum_if_even(xs):
    s = 0
    for x in xs:
        if x % 2 != 0:
            continue
        s += x
    return s
