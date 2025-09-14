def sum_if_even(xs):
    total = 0
    for x in xs:
        if x % 2 == 0:
            total += x
    return total

