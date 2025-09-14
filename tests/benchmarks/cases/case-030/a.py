def argmin(xs):
    best_i = 0
    best_v = xs[0]
    for i in range(1, len(xs)):
        if xs[i] < best_v:
            best_v = xs[i]
            best_i = i
    return best_i

