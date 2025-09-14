def parse_ints(lines):
    out = []
    for s in lines:
        s = s.strip()
        if s:
            out.append(int(s))
    return out
