def unique_order(xs):
    seen = set()
    out = []
    for x in xs:
        if x in seen:
            continue
        out.append(x)
        seen.add(x)
    return out

