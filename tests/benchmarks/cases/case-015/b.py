def combine_dicts(left, right):
    res = dict(left)
    for key, val in right.items():
        res[key] = val
    return res
