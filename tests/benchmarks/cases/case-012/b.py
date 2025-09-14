def flatten_lists(xss):
    res = []
    for xs in xss:
        for x in xs:
            res.append(x)
    return res
