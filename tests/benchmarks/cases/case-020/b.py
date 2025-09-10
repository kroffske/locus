def to_ints(texts):
    res = []
    for t in texts:
        t = t.strip()
        if t:
            res.append(int(t))
    return res

