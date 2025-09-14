def merge_keys(d1, d2):
    out = dict(d1)
    for k, v in d2.items():
        out[k] = v
    return out

