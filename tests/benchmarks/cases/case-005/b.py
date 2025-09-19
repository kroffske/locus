def max_in_list(xs):
    m = xs[0]
    for v in xs[1:]:
        if v > m:  # same logic
            m = v
    return m
