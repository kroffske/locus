def fact(n):
    r = 1  # init
    for i in range(2, n + 1):
        r *= i
    return r
