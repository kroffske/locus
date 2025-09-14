def join_path(parts):
    out = ""
    for p in parts:
        if not out:
            out = p.strip("/")
        else:
            out += "/" + p.strip("/")
    return out
